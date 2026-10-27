import re
import os
import logging
import requests
from django.db.models import Q
from .models import FAQ, ErrorCode, SupportTicket
from .mongo import log_chat_interaction

logger = logging.getLogger(__name__)

# Third-party Currency Rates with strict 2.0s timeout and offline fallback
FALLBACK_RATES = {
    'base': 'USD',
    'date': '2026-10-27',
    'is_fallback': True,
    'source': 'offline_benchmark_rates',
    'rates': {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'INR': 83.25,
        'CAD': 1.36,
        'AUD': 1.52,
        'JPY': 151.40,
        'CHF': 0.88,
    }
}


def get_live_exchange_rates(base_currency='USD'):
    """
    Fetches real-time currency exchange rates with a strict 2.0s time limit and fallback.
    Fails safely to cached offline rates if the third-party API is slow or unreachable.
    """
    url = f"https://open.er-api.com/v6/latest/{base_currency}"
    try:
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            filtered_rates = {
                curr: rates.get(curr)
                for curr in ['USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD', 'JPY', 'CHF']
                if curr in rates
            }
            return {
                'base': base_currency,
                'date': data.get('time_last_update_utc', 'latest'),
                'is_fallback': False,
                'source': 'open.er-api.com',
                'rates': filtered_rates or FALLBACK_RATES['rates']
            }
    except requests.exceptions.Timeout:
        logger.warning("Third-party Exchange Rate API timed out (>2.0s); using fallback rates.")
    except Exception as e:
        logger.warning(f"Third-party Exchange Rate API failed ({e}); using fallback rates.")

    return FALLBACK_RATES


def query_gemini_api(user_message, context_text=""):
    """
    Optional enhancement: calls Gemini API if GEMINI_API_KEY is present in environment.
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None

    try:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            "You are ExpenseFlow AI, a helpful, polite assistant embedded inside the ExpenseFlow web application. "
            "Help the user with managing personal finances, tracking expenses, explaining error codes, and answering FAQs.\n\n"
            f"Context Data:\n{context_text}\n\n"
            f"User Question: {user_message}\n\n"
            "Provide a concise, clear answer. If the question cannot be answered from the app's features, offer to create a support ticket."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        res = requests.post(endpoint, json=payload, timeout=4.0)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get('candidates', [])
            if candidates:
                return candidates[0]['content']['parts'][0]['text']
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}")
    return None


def process_chat_message(user_message, user=None, session_id='guest'):
    """
    Core AI Assistant Logic:
    1. Detects Error Codes (400, 401, 403, 404, 429, 500, 503, EXP-4001, etc.)
    2. Answers from FAQ SQL database
    3. Detects Support Ticket creation intent or creates support ticket when it cannot answer
    4. Logs conversation and intent to MongoDB
    """
    text = (user_message or '').strip()
    lower_text = text.lower()

    reply = ""
    intent = "general"
    ticket_created = False
    ticket_id = None
    suggested_actions = []

    # 1. Check for Error Codes (both standard HTTP and custom EXP- codes)
    # Search for codes like 400, 401, 403, 404, 429, 500, 503, EXP-4001, EXP-4002
    code_match = re.search(r'\b(exp-\d{4}|400|401|403|404|429|500|503)\b', lower_text)
    error_obj = None

    if code_match:
        matched_code = code_match.group(1).upper()
        error_obj = ErrorCode.objects.filter(code__iexact=matched_code, is_active=True).first()
    elif 'error' in lower_text or 'code' in lower_text:
        # Check all active error codes
        for err in ErrorCode.objects.filter(is_active=True):
            if err.code.lower() in lower_text:
                error_obj = err
                break

    if error_obj:
        intent = "error_code"
        reply = (
            f"⚠️ **Error {error_obj.code}: {error_obj.title}** ({error_obj.get_category_display()})\n\n"
            f"**What it means:** {error_obj.description}\n\n"
            f"💡 **Recommended Solution:** {error_obj.solution}\n\n"
            f"Would you like me to open a support ticket for this error?"
        )
        suggested_actions = [
            {"label": "Open Support Ticket", "action": "create_ticket", "subject": f"Assistance with Error {error_obj.code}"},
            {"label": "View Error Directory", "action": "navigate", "url": "/faq/#error-codes"},
            {"label": "Back to Dashboard", "action": "navigate", "url": "/"}
        ]

    # 2. Check for explicit Ticket Creation Intent
    elif any(phrase in lower_text for phrase in [
        'create ticket', 'open ticket', 'support ticket', 'file a ticket',
        'talk to human', 'human agent', 'contact support', 'submit ticket',
        'file a complaint', 'talk to support', 'reach support'
    ]):
        intent = "ticket_creation"
        # Auto-create or prompt ticket
        email = user.email if (user and user.is_authenticated and user.email) else 'user@expenseflow.local'
        subject = text[:100]
        ticket = SupportTicket.objects.create(
            user=user if (user and user.is_authenticated) else None,
            name=user.username if (user and user.is_authenticated) else 'Guest User',
            email=email,
            subject=f"Inquiry: {subject}",
            description=f"Auto-generated from AI Assistant chat.\nUser Query: {text}",
            priority='medium',
            source='ai_assistant'
        )
        ticket_created = True
        ticket_id = ticket.ticket_id
        reply = (
            f"🎫 **Support Ticket Created: {ticket.ticket_id}**\n\n"
            f"I have opened a support ticket for you with priority **{ticket.priority.capitalize()}**. "
            f"Our technical support team has received your inquiry: *\"{ticket.subject}\"*\n\n"
            f"We will review your request and follow up shortly at `{ticket.email}`."
        )
        suggested_actions = [
            {"label": "View Support Tickets", "action": "navigate", "url": "/support/"},
            {"label": "Ask Another Question", "action": "chat", "message": "What features are available?"}
        ]

    # 3. Check FAQ Knowledge Base
    else:
        # Search FAQs
        tokens = [t for t in re.findall(r'\w+', lower_text) if len(t) > 2]
        faqs = FAQ.objects.filter(is_active=True)

        best_faq = None
        best_score = 0

        for faq in faqs:
            q_lower = faq.question.lower()
            a_lower = faq.answer.lower()
            score = 0
            for token in tokens:
                if token in q_lower:
                    score += 3
                elif token in a_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_faq = faq

        if best_faq and best_score >= 3:
            intent = "faq"
            reply = (
                f"📋 **{best_faq.question}**\n\n"
                f"{best_faq.answer}\n\n"
                f"*(Category: {best_faq.get_category_display()})*"
            )
            suggested_actions = [
                {"label": "View All FAQs", "action": "navigate", "url": "/faq/"},
                {"label": "Add Expense", "action": "navigate", "url": "/expenses/add/"},
                {"label": "Check Budgets", "action": "navigate", "url": "/budgets/"}
            ]
        else:
            # 4. Unknown Query: Try Gemini API or auto-generate Support Ticket
            context_faqs = "\n".join([f"Q: {f.question}\nA: {f.answer}" for f in faqs[:6]])
            gemini_reply = query_gemini_api(user_message, context_faqs)

            if gemini_reply:
                intent = "ai_gemini"
                reply = gemini_reply
                suggested_actions = [
                    {"label": "Create Support Ticket", "action": "create_ticket", "subject": text[:80]},
                    {"label": "Browse FAQs", "action": "navigate", "url": "/faq/"}
                ]
            else:
                # Requirement: "creates a support ticket when it cannot answer"
                intent = "ticket_fallback"
                email = user.email if (user and user.is_authenticated and user.email) else 'guest@expenseflow.local'
                ticket = SupportTicket.objects.create(
                    user=user if (user and user.is_authenticated) else None,
                    name=user.username if (user and user.is_authenticated) else 'Guest Visitor',
                    email=email,
                    subject=f"Unresolved AI Query: {text[:80]}",
                    description=f"User asked a question the AI assistant could not resolve.\nQuery: {text}",
                    priority='medium',
                    source='ai_assistant_fallback'
                )
                ticket_created = True
                ticket_id = ticket.ticket_id
                reply = (
                    f"🤖 I couldn't find a direct answer in our FAQs or Error Code directory for: *\"{text}\"*.\n\n"
                    f"I have automatically created a support ticket for you:\n"
                    f"🎫 **Ticket ID: {ticket.ticket_id}**\n"
                    f"Status: **Open** | Contact: `{ticket.email}`\n\n"
                    f"A human support representative will review your question and respond shortly. "
                    f"In the meantime, feel free to browse our FAQ page or ask about an error code like `404` or `500`!"
                )
                suggested_actions = [
                    {"label": "View All FAQs", "action": "navigate", "url": "/faq/"},
                    {"label": "View Support Tickets", "action": "navigate", "url": "/support/"},
                    {"label": "Explain 404 Error", "action": "chat", "message": "Explain error 404"}
                ]

    # Log interaction to MongoDB
    user_id = user.id if (user and user.is_authenticated) else None
    log_chat_interaction(
        session_id=session_id,
        user_message=text,
        bot_response=reply,
        intent=intent,
        user_id=user_id,
        metadata={
            'ticket_created': ticket_created,
            'ticket_id': ticket_id,
        }
    )

    return {
        'reply': reply,
        'intent': intent,
        'ticket_created': ticket_created,
        'ticket_id': ticket_id,
        'suggested_actions': suggested_actions,
    }
