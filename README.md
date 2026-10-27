# ExpenseFlow - Intelligent Full-Stack Expense Tracker & AI Assistant

A full-stack personal finance and expense management web application featuring a dedicated **AI Assistant**, SQL-backed **Frequently Asked Questions (FAQs)**, comprehensive **Error Code Directory (400, 401, 403, 404, 429, 500, 503, EXP-4001, EXP-4002)**, SQL-based **Support Ticket Management**, **MongoDB Chat Logging & Feedback**, **Request Performance Logging**, **System Health Monitoring**, and a **Live Third-Party Currency Exchange API** with fallback.

[![Live Website](https://img.shields.io/badge/Live%20Website-HTTPS%20Online-brightgreen?style=for-the-badge&logo=render&logoColor=white)](https://expense-tracker-web.onrender.com)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Nirmal61022%2Fexpense--tracker-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Nirmal61022/expense-tracker)
[![Tests](https://img.shields.io/badge/Automated%20Tests-28%20Passed-4c1?style=for-the-badge&logo=pytest)](file:///c:/Users/nirma/Documents/expense-tracker/expenses/tests.py)

---

## 📋 Final Assessment Submission Details

| Field | Detail |
| :--- | :--- |
| **Individual Task Title** | Personal Financial Dashboard with Integrated AI Assistant, SQL Knowledge Base, and MongoDB Analytics |
| **Live Website Link (HTTPS)** | **[https://expense-tracker-web.onrender.com](https://expense-tracker-web.onrender.com)** |
| **GitHub Repository Link** | **[https://github.com/Nirmal61022/expense-tracker](https://github.com/Nirmal61022/expense-tracker)** |
| **Health Check Endpoint** | **[https://expense-tracker-web.onrender.com/health/](https://expense-tracker-web.onrender.com/health/)** |
| **Automated Test Results** | **28 / 28 Automated Tests Passed** (`python manage.py test`) |

---

## 🌟 Assessment Requirements & Implementation

### 1. Responsive Website with 5+ Pages & Global Chat Widget
- **Dashboard (`/`)**: Key performance indicators (Today's, Month's, Year's, and Total spend), dynamic budget threshold progress alerts, Chart.js doughnut & daily trend charts, and recent transaction log.
- **All Expenses (`/expenses/`)**: Advanced multi-field filtering (category, payment method, date range, amount range), search, sorting, pagination, and CSV data export.
- **Monthly Reports (`/report/`)**: Month/Year selector, daily spending timeline chart, category breakdown table, and peak expense analysis.
- **Budget Planner (`/budgets/`)**: Month-by-month spending limits with real-time remaining calculations and status badges.
- **FAQ & Error Codes Directory (`/faq/`)**: 12 categorized FAQs and 9 documented error codes with interactive search.
- **Support Tickets Portal (`/support/`)**: View tickets, submit inquiries, and track ticket resolutions.
- **Floating AI Chat Widget**: Embedded globally via `base.html` so users can chat with the assistant from **every single page** on desktop, tablet, and mobile devices.

### 2. 12 FAQs Stored in SQL Database
- Minimum requirement: 10 FAQs. **Implemented: 12 detailed FAQs** stored in SQL (`expenses_faq` table) with categories: *Getting Started, Expenses, Budgets, Reports, Account & Security, Troubleshooting*.
- Searchable on the `/faq/` page and queried in real-time by the AI Assistant.

### 3. 9 Error Codes (HTTP + Site-Specific)
- Minimum requirement: 8 error codes (400, 401, 403, 404, 429, 500, 503 + site-specific). **Implemented: 9 error codes** stored in SQL (`expenses_errorcode` table):
  1. `400 Bad Request` — Client syntax / malformed input validation failure.
  2. `401 Unauthorized` — Authentication credentials missing or invalid.
  3. `403 Forbidden` — Cross-user data boundary access attempt.
  4. `404 Not Found` — Requested endpoint or resource does not exist.
  5. `429 Too Many Requests` — Client rate limit exceeded.
  6. `500 Internal Server Error` — Unhandled server-side condition.
  7. `503 Service Unavailable` — Service temporarily overloaded or in maintenance.
  8. `EXP-4001 Budget Overrun` — *Site-Specific*: Expense causes monthly budget overrun.
  9. `EXP-4002 Invalid Ledger Amount` — *Site-Specific*: Negative or zero currency amount submitted.

### 4. Custom 404 & 500 Pages with "Ask the Assistant"
- Custom `404.html` and `500.html` styled with accessible, responsive layouts.
- Both pages feature an **"Ask the Assistant"** option (`window.openAssistantWithPrompt(...)`) that immediately launches the AI chat widget with prefilled context about the error.

### 5. AI Assistant Capabilities
- **FAQ Answering**: Matches user questions against SQL FAQ knowledge base with keyword similarity scoring.
- **Error Code Explanations**: Detects HTTP or application error codes (e.g. "Explain error 404", "What is 500?", "EXP-4001") and provides root cause analysis and step-by-step remediation.
- **Automatic Support Ticket Creation**: When a question cannot be resolved or when the user asks for a human agent, the assistant automatically creates a `SupportTicket` in SQL and returns a tracking ID (e.g. `TCK-XXXXXX`).
- **Optional Gemini API Augmentation**: Uses Google Gemini API (`gemini-1.5-flash`) when `GEMINI_API_KEY` is present.

### 6. Dual-Database Storage Architecture (SQL + MongoDB)
- **SQL Database (PostgreSQL / SQLite)**:
  - User accounts and authentication sessions.
  - Financial records (`Expense`, `MonthlyBudget`).
  - Knowledge base (`FAQ`, `ErrorCode`).
  - Support desk (`SupportTicket`).
- **MongoDB (NoSQL Document Store)**:
  - `chat_logs`: Session ID, user ID, user query, bot reply, matched intent, and timestamps.
  - `chat_feedback`: User ratings (thumbs up/down) and qualitative feedback comments.
  - Resilient fallback: If MongoDB is offline, requests continue smoothly with zero interruption via an in-memory fallback buffer.

### 7. Request Performance Logging & Health Check Endpoint
- **Request Logging Middleware (`expenses.middleware.RequestLoggingMiddleware`)**: Intercepts all requests and logs HTTP method, route, status code, response time in milliseconds, client IP address, and authenticated user. Adds `X-Response-Time` header.
- **Health Check Page (`/health/`)**: Returns JSON diagnostic status of the SQL database connection, MongoDB status, service uptime, and API version with HTTP 200.

### 8. Third-Party API with Time Limit and Fallback
- **Live Currency Exchange Rates API**: Fetches real-time foreign exchange conversions from `https://open.er-api.com/v6/latest/USD` with a strict **2.0-second timeout** (`requests.get(url, timeout=2.0)`).
- **Graceful Fallback**: If the external API times out, fails, or the server is offline, it immediately serves curated offline benchmark exchange rates (`is_fallback: true`), ensuring the user interface never freezes.

---

## 💡 Proposed Improvement

**Automated Receipt OCR & Predictive Expense Categorization**:
Integrate an optical character recognition (OCR) and lightweight computer vision model (e.g., Google Document AI or Tesseract) allowing users to take a photo of paper receipts from mobile devices. The system would automatically extract the merchant name, date, tax, and total amount, use natural language classification to suggest the correct expense category (e.g. *Groceries* -> *Food*), and predict whether the transaction will cause a monthly budget overrun before the user commits it.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+ / Django 5+ / 6+
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript, Chart.js, Font Awesome 6
- **Relational Database**: PostgreSQL (Production) / SQLite3 (Local)
- **Document Database**: MongoDB (Chat logs & user ratings via `pymongo`)
- **Third-Party API**: Open Exchange Rates API (with 2.0s timeout & fallback)
- **Application Server**: Gunicorn
- **Static Asset Pipeline**: WhiteNoise (Manifest compression & caching)
- **Cloud Hosting**: Render

---

## 🧪 Automated Test Suite (28 Tests)

Execute the complete test suite:
```bash
python manage.py test
```

```text
Ran 28 tests in 15.196s

OK
Destroying test database for alias 'default'...
Found 28 test(s).
System check identified no issues (0 silenced).
```

---

## 🚀 Local Setup Instructions

```bash
# 1. Clone repository
git clone https://github.com/Nirmal61022/expense-tracker.git
cd expense-tracker

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows

# 3. Install requirements
pip install -r requirements.txt

# 4. Run migrations (seeds 12 FAQs and 9 Error Codes automatically)
python manage.py migrate

# 5. Run test suite
python manage.py test

# 6. Start server
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.
