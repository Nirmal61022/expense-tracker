import csv
import json
from decimal import Decimal
from datetime import datetime, date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Avg, Max
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Expense, MonthlyBudget, ExpenseCategory, PaymentMethod, FAQ, ErrorCode, SupportTicket
from .forms import UserRegistrationForm, ExpenseForm, MonthlyBudgetForm
from .services import process_chat_message, get_live_exchange_rates
from .mongo import log_chat_feedback, check_mongo_health
from django.views.decorators.csrf import csrf_exempt
from django.db import connection


def register_view(request):
    if request.user.is_authenticated:
        return redirect('expenses:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Log user in directly
            login(request, user)
            messages.success(request, f"Welcome to Expense Tracker, {user.username}! Your account is ready.")
            return redirect('expenses:dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'expenses/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('expenses:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('expenses:dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'expenses/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('expenses:login')


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    # Total expenses today
    today_total = Expense.objects.filter(
        user=user, date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Total expenses this month
    month_qs = Expense.objects.filter(
        user=user, date__year=current_year, date__month=current_month
    )
    month_total = month_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_transactions = month_qs.count()

    # Total expenses this year
    year_total = Expense.objects.filter(
        user=user, date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Total all-time transactions
    all_time_transactions = Expense.objects.filter(user=user).count()

    # Monthly Budget Check
    budget_obj = MonthlyBudget.objects.filter(
        user=user, year=current_year, month=current_month
    ).first()

    budget_amount = budget_obj.amount if budget_obj else None
    budget_remaining = None
    budget_percentage = 0
    budget_status = 'no_budget'  # 'safe', 'warning', 'danger', 'no_budget'

    if budget_amount and budget_amount > 0:
        budget_remaining = budget_amount - month_total
        budget_percentage = float((month_total / budget_amount) * 100)
        if month_total > budget_amount:
            budget_status = 'danger'
        elif budget_percentage >= 80:
            budget_status = 'warning'
        else:
            budget_status = 'safe'

    # Recent transactions
    recent_expenses = Expense.objects.filter(user=user).order_by('-date', '-created_at')[:7]

    # Category breakdown for current month (Chart 1)
    category_data = (
        month_qs.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    cat_labels = [item['category'] for item in category_data]
    cat_values = [float(item['total']) for item in category_data]

    # Daily spending for the current month (Chart 2)
    daily_data = (
        month_qs.values('date')
        .annotate(total=Sum('amount'))
        .order_by('date')
    )
    day_labels = [item['date'].strftime('%b %d') for item in daily_data]
    day_values = [float(item['total']) for item in daily_data]

    context = {
        'today': today,
        'today_total': today_total,
        'month_total': month_total,
        'month_transactions': month_transactions,
        'year_total': year_total,
        'all_time_transactions': all_time_transactions,
        'budget_amount': budget_amount,
        'budget_remaining': budget_remaining,
        'budget_percentage': round(min(budget_percentage, 100), 1),
        'raw_percentage': round(budget_percentage, 1),
        'budget_status': budget_status,
        'recent_expenses': recent_expenses,
        'cat_labels_json': json.dumps(cat_labels),
        'cat_values_json': json.dumps(cat_values),
        'day_labels_json': json.dumps(day_labels),
        'day_values_json': json.dumps(day_values),
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def expense_list_view(request):
    user = request.user
    expenses = Expense.objects.filter(user=user)

    # Filter parameters
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    payment_method = request.GET.get('payment_method', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    min_amount = request.GET.get('min_amount', '').strip()
    max_amount = request.GET.get('max_amount', '').strip()
    sort_by = request.GET.get('sort', '-date').strip()

    if q:
        expenses = expenses.filter(merchant__icontains=q) | expenses.filter(notes__icontains=q)

    if category:
        expenses = expenses.filter(category=category)

    if payment_method:
        expenses = expenses.filter(payment_method=payment_method)

    if date_from:
        try:
            expenses = expenses.filter(date__gte=date_from)
        except Exception:
            pass

    if date_to:
        try:
            expenses = expenses.filter(date__lte=date_to)
        except Exception:
            pass

    if min_amount:
        try:
            expenses = expenses.filter(amount__gte=Decimal(min_amount))
        except Exception:
            pass

    if max_amount:
        try:
            expenses = expenses.filter(amount__lte=Decimal(max_amount))
        except Exception:
            pass

    # Sorting
    allowed_sorts = {
        '-date': '-date',
        'date': 'date',
        '-amount': '-amount',
        'amount': 'amount',
        'merchant': 'merchant',
        '-merchant': '-merchant'
    }
    expenses = expenses.order_by(allowed_sorts.get(sort_by, '-date'), '-created_at')

    # Total for filtered set
    filtered_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    filtered_count = expenses.count()

    # Pagination
    paginator = Paginator(expenses, 12)  # 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Construct clean query string without page for pagination links
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    query_string = params.urlencode()

    context = {
        'page_obj': page_obj,
        'filtered_total': filtered_total,
        'filtered_count': filtered_count,
        'categories': ExpenseCategory.choices,
        'payment_methods': PaymentMethod.choices,
        'current_filters': {
            'q': q,
            'category': category,
            'payment_method': payment_method,
            'date_from': date_from,
            'date_to': date_to,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'sort': sort_by,
        },
        'query_string': query_string,
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_create_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, f"Expense of ${expense.amount} for '{expense.merchant}' added successfully!")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'action_title': 'Add New Expense',
        'button_text': 'Save Expense',
    })


@login_required
def expense_update_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense for '{expense.merchant}' updated successfully!")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'action_title': 'Edit Expense',
        'button_text': 'Update Expense',
        'expense': expense,
    })


@login_required
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == 'POST':
        merchant_name = expense.merchant
        amount = expense.amount
        expense.delete()
        messages.success(request, f"Expense '{merchant_name}' (${amount}) was deleted.")
        return redirect('expenses:expense_list')

    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


@login_required
def monthly_report_view(request):
    user = request.user
    today = timezone.now().date()

    # Selected month and year
    try:
        selected_year = int(request.GET.get('year', today.year))
        selected_month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        selected_year = today.year
        selected_month = today.month

    # Clamp month
    if not (1 <= selected_month <= 12):
        selected_month = today.month

    # Get user available years
    available_years = list(
        Expense.objects.filter(user=user)
        .dates('date', 'year', order='DESC')
        .values_list('date__year', flat=True)
    )
    if today.year not in available_years:
        available_years.insert(0, today.year)
    available_years = sorted(list(set(available_years)), reverse=True)

    # Monthly queryset
    month_qs = Expense.objects.filter(
        user=user, date__year=selected_year, date__month=selected_month
    )

    total_spent = month_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_count = month_qs.count()

    # Category breakdown
    category_summary = (
        month_qs.values('category')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    # Calculate percentages
    category_breakdown = []
    top_category = None
    for item in category_summary:
        cat_pct = round((float(item['total']) / float(total_spent) * 100), 1) if total_spent > 0 else 0
        category_breakdown.append({
            'category': item['category'],
            'total': item['total'],
            'count': item['count'],
            'percentage': cat_pct,
        })
    if category_breakdown:
        top_category = category_breakdown[0]['category']

    # Daily breakdown for report
    daily_summary = (
        month_qs.values('date')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('date')
    )
    highest_day = None
    highest_day_amount = Decimal('0.00')
    for d in daily_summary:
        if d['total'] > highest_day_amount:
            highest_day_amount = d['total']
            highest_day = d['date']

    # Days in month with spending for average calculation
    distinct_active_days = len(daily_summary)
    daily_average = (
        round(total_spent / Decimal(distinct_active_days), 2)
        if distinct_active_days > 0 else Decimal('0.00')
    )

    # Budget for this month
    budget = MonthlyBudget.objects.filter(
        user=user, year=selected_year, month=selected_month
    ).first()

    budget_info = None
    if budget:
        remaining = budget.amount - total_spent
        pct = round((float(total_spent) / float(budget.amount) * 100), 1) if budget.amount > 0 else 0
        budget_info = {
            'amount': budget.amount,
            'remaining': remaining,
            'percentage': pct,
            'is_exceeded': total_spent > budget.amount,
        }

    # Chart data
    cat_labels = [item['category'] for item in category_breakdown]
    cat_values = [float(item['total']) for item in category_breakdown]

    day_labels = [item['date'].strftime('%d %b') for item in daily_summary]
    day_values = [float(item['total']) for item in daily_summary]

    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    month_name = dict(months).get(selected_month, 'Unknown')

    context = {
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_month_name': month_name,
        'available_years': available_years,
        'months': months,
        'total_spent': total_spent,
        'total_count': total_count,
        'daily_average': daily_average,
        'highest_day': highest_day,
        'highest_day_amount': highest_day_amount,
        'top_category': top_category,
        'category_breakdown': category_breakdown,
        'daily_summary': daily_summary,
        'budget_info': budget_info,
        'cat_labels_json': json.dumps(cat_labels),
        'cat_values_json': json.dumps(cat_values),
        'day_labels_json': json.dumps(day_labels),
        'day_values_json': json.dumps(day_values),
    }
    return render(request, 'expenses/monthly_report.html', context)


@login_required
def budget_manage_view(request):
    user = request.user
    today = timezone.now().date()

    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST)
        if form.is_valid():
            year = form.cleaned_data['year']
            month = form.cleaned_data['month']
            amount = form.cleaned_data['amount']

            budget, created = MonthlyBudget.objects.update_or_create(
                user=user,
                year=year,
                month=month,
                defaults={'amount': amount}
            )
            action = "created" if created else "updated"
            messages.success(request, f"Budget for {year}/{month:02d} {action} successfully (${amount}).")
            return redirect('expenses:budget_manage')
    else:
        form = MonthlyBudgetForm(initial={
            'year': today.year,
            'month': today.month,
        })

    # List all user budgets with actual spending stats
    budgets = MonthlyBudget.objects.filter(user=user).order_by('-year', '-month')
    budget_cards = []
    for b in budgets:
        spent = Expense.objects.filter(
            user=user, date__year=b.year, date__month=b.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        remaining = b.amount - spent
        pct = round((float(spent) / float(b.amount) * 100), 1) if b.amount > 0 else 0
        budget_cards.append({
            'obj': b,
            'spent': spent,
            'remaining': remaining,
            'percentage': min(pct, 100),
            'raw_percentage': pct,
            'is_over': spent > b.amount,
            'is_warning': (pct >= 80 and spent <= b.amount),
        })

    return render(request, 'expenses/budget_manage.html', {
        'form': form,
        'budget_cards': budget_cards,
    })


@login_required
def budget_delete_view(request, pk):
    budget = get_object_or_404(MonthlyBudget, pk=pk, user=request.user)
    if request.method == 'POST':
        year = budget.year
        month = budget.month
        budget.delete()
        messages.success(request, f"Budget for {year}/{month:02d} was deleted.")
    return redirect('expenses:budget_manage')


@login_required
def export_csv_view(request):
    user = request.user
    expenses = Expense.objects.filter(user=user)

    # Apply any active query filters to export
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    payment_method = request.GET.get('payment_method', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if q:
        expenses = expenses.filter(merchant__icontains=q) | expenses.filter(notes__icontains=q)
    if category:
        expenses = expenses.filter(category=category)
    if payment_method:
        expenses = expenses.filter(payment_method=payment_method)
    if date_from:
        try:
            expenses = expenses.filter(date__gte=date_from)
        except Exception:
            pass
    if date_to:
        try:
            expenses = expenses.filter(date__lte=date_to)
        except Exception:
            pass

    response = HttpResponse(content_type='text/csv')
    filename = f"expenses_{user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Merchant / Description', 'Category', 'Payment Method', 'Amount ($)', 'Notes'])

    for exp in expenses.order_by('-date'):
        writer.writerow([
            exp.date.strftime('%Y-%m-%d'),
            exp.merchant,
            exp.category,
            exp.payment_method,
            f"{exp.amount:.2f}",
            exp.notes,
        ])

    return response


def faq_view(request):
    """
    Displays the FAQ and Error Codes reference directory.
    Supports search query parameter ?q=
    """
    query = request.GET.get('q', '').strip()
    faqs = FAQ.objects.filter(is_active=True)
    error_codes = ErrorCode.objects.filter(is_active=True)

    if query:
        faqs = faqs.filter(Q(question__icontains=query) | Q(answer__icontains=query))
        error_codes = error_codes.filter(
            Q(code__icontains=query) | Q(title__icontains=query) |
            Q(description__icontains=query) | Q(solution__icontains=query)
        )

    # Group FAQs by category
    categories = [
        ('getting_started', 'Getting Started'),
        ('expenses', 'Expenses & Transactions'),
        ('budgets', 'Budgets & Limits'),
        ('reports', 'Reports & Analytics'),
        ('account', 'Account & Security'),
        ('troubleshooting', 'Troubleshooting'),
    ]

    faq_grouped = []
    for cat_key, cat_name in categories:
        cat_items = [f for f in faqs if f.category == cat_key]
        if cat_items:
            faq_grouped.append({'name': cat_name, 'key': cat_key, 'items': cat_items})

    context = {
        'faq_grouped': faq_grouped,
        'all_faqs': faqs,
        'error_codes': error_codes,
        'query': query,
        'total_faqs': faqs.count(),
        'total_errors': error_codes.count(),
    }
    return render(request, 'expenses/faq.html', context)


def support_ticket_view(request):
    """
    Allows users to view their support tickets or create a new support ticket.
    Stored in SQL database.
    """
    user = request.user if request.user.is_authenticated else None

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        priority = request.POST.get('priority', 'medium')

        if not email and user and user.email:
            email = user.email
        if not name and user:
            name = user.username

        if subject and description and email:
            ticket = SupportTicket.objects.create(
                user=user,
                name=name or 'Guest',
                email=email,
                subject=subject,
                description=description,
                priority=priority if priority in ['low', 'medium', 'high', 'urgent'] else 'medium',
                source='web_portal'
            )
            messages.success(request, f"Support ticket #{ticket.ticket_id} created successfully! Our team will contact you at {ticket.email}.")
            return redirect('expenses:support_tickets')
        else:
            messages.error(request, "Please fill in all required fields (Email, Subject, Description).")

    # Fetch user's tickets if authenticated, or recent tickets for guest session
    tickets = []
    if user:
        tickets = SupportTicket.objects.filter(user=user).order_by('-created_at')

    return render(request, 'expenses/support_tickets.html', {
        'tickets': tickets,
    })


@csrf_exempt
def api_chat_view(request):
    """
    API endpoint for the AI Assistant floating widget.
    Processes user input, queries FAQs, explains error codes, or opens support ticket.
    Logs interaction to MongoDB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    message = data.get('message', '').strip()
    session_id = data.get('session_id') or request.session.session_key or 'anonymous-session'

    if not message:
        return JsonResponse({'error': 'Message content is required'}, status=400)

    user = request.user if request.user.is_authenticated else None
    response_data = process_chat_message(user_message=message, user=user, session_id=session_id)

    return JsonResponse(response_data)


@csrf_exempt
def api_chat_feedback_view(request):
    """
    API endpoint to record thumbs-up / thumbs-down ratings and user feedback in MongoDB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    session_id = data.get('session_id') or request.session.session_key or 'anonymous'
    rating = data.get('rating', 1)
    comments = data.get('comments', '')
    user_id = request.user.id if request.user.is_authenticated else None

    inserted_id = log_chat_feedback(session_id=session_id, rating=rating, comments=comments, user_id=user_id)
    return JsonResponse({'status': 'success', 'feedback_id': inserted_id})


def api_exchange_rates_view(request):
    """
    Third-party API endpoint with a strict 2.0s time limit and fallback offline dataset.
    """
    base = request.GET.get('base', 'USD').upper()
    data = get_live_exchange_rates(base_currency=base)
    return JsonResponse(data)


def health_check_view(request):
    """
    Health check endpoint for monitoring uptime, SQL database connection, and MongoDB status.
    """
    health_data = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'ExpenseFlow Web Application',
        'version': '1.1.0',
        'checks': {}
    }

    # 1. SQL Database Check
    try:
        connection.ensure_connection()
        health_data['checks']['sql_database'] = {
            'status': 'ok',
            'engine': connection.settings_dict['ENGINE'].split('.')[-1],
        }
    except Exception as e:
        health_data['status'] = 'degraded'
        health_data['checks']['sql_database'] = {
            'status': 'error',
            'error': str(e)
        }

    # 2. MongoDB Check
    mongo_status = check_mongo_health()
    health_data['checks']['mongodb'] = mongo_status

    status_code = 200 if health_data['status'] == 'healthy' else 503
    return JsonResponse(health_data, status=status_code)


def custom_404_view(request, exception=None):
    """
    Custom 404 Page Not Found with 'Ask the assistant' option.
    """
    return render(request, 'expenses/404.html', {
        'requested_path': request.path,
    }, status=404)


def custom_500_view(request):
    """
    Custom 500 Internal Server Error with 'Ask the assistant' option.
    """
    return render(request, 'expenses/500.html', {
        'requested_path': request.path,
    }, status=500)

