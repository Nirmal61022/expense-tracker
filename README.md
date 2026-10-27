# ExpenseFlow - Professional Full-Stack Expense Tracker

A full-stack financial dashboard and expense tracking web application built with **Python Django**, **Tailwind CSS**, **Chart.js**, and deployed to **Render** with **PostgreSQL**.

[![Render Deployment](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com)
[![Django](https://img.shields.io/badge/Django-6.1%2F5.0-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-brightgreen?style=flat&logo=pytest)](file:///c:/Users/nirma/Documents/expense-tracker/expenses/tests.py)

---

## 🌟 Core Features

1. **User Authentication & Absolute Data Isolation**:
   - Secure registration, login, and logout.
   - Every single expense and budget is strictly tied to the authenticated user. User A cannot view, edit, or delete User B's records.
2. **Interactive Financial Dashboard**:
   - Real-time spending metrics: Today's spend, this month's spend, this year's spend, and total transaction volume.
   - Dynamic monthly budget status progress bar with threshold alerts (Safe, Warning at 80%+, Danger when exceeded).
   - Recent transactions table with category badges and one-click edit/delete triggers.
   - Interactive Chart.js charts: Category distribution doughnut chart & monthly daily spending trend line chart.
3. **Expense Management**:
   - Add, edit, and delete transactions with positive `DecimalField` amounts and server-side validation.
   - Modal and page confirmation before any deletion to prevent accidental loss.
   - Pre-configured categories: Food, Transport, Education, Shopping, Bills, Healthcare, Entertainment, Travel, and Other.
   - Payment methods: Cash, Credit Card, Debit Card, UPI / Digital Wallet, Bank Transfer, Other.
4. **Search, Advanced Filtering & Pagination**:
   - Keyword search across merchant descriptions and optional notes.
   - Multi-criteria filter by category, payment method, date range (from/to), and amount range (min/max).
   - Flexible sorting (Date, Amount, Merchant).
   - Clean 12-item pagination preserving active filter queries.
5. **Monthly Expense Reports**:
   - Selector for any month and year.
   - Monthly summary metrics: Total spend, active daily average, peak spending day, and top spending category.
   - Category distribution doughnut chart and daily spending bar chart.
   - Detailed category breakdown table with percentage share bars.
6. **Budget Planner**:
   - Set monthly spending limits per month/year.
   - Real-time tracking of remaining amounts and visual progress bars.
7. **CSV Data Export**:
   - Download transaction history in standard CSV format, respecting active search and filter constraints.
8. **Modern Fintech UI**:
   - Responsive layout designed for mobile, tablet, and desktop screens with collapsable sidebar navigation, high-contrast readable typography, and accessible color schemes.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+ / Django 5+ / 6+
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript, Chart.js, Font Awesome 6
- **Database**:
  - Development: SQLite3
  - Production: PostgreSQL (via `dj-database-url` and `psycopg`)
- **Production Server**: Gunicorn
- **Static Assets**: WhiteNoise with compression and caching
- **Deployment Platform**: Render (Web Service + Managed PostgreSQL Database)
- **Version Control**: Git & GitHub

---

## 🚀 Local Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/Nirmal61022/expense-tracker.git
cd expense-tracker
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py migrate
```

### 5. Run automated tests
```bash
python manage.py test
```

### 6. Start the local development server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🌐 Production Deployment on Render

This project is configured for Render Blueprint deployment via `render.yaml`.

### 1-Click Render Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Nirmal61022/expense-tracker)

### Manual Blueprint Setup:
1. Log in to [Render](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub account and select repository `Nirmal61022/expense-tracker`.
4. Render will detect `render.yaml` and automatically provision:
   - **PostgreSQL Database** (`expense-tracker-db`) on the free tier.
   - **Python Web Service** (`expense-tracker-web`) running `./build.sh` and `gunicorn expense_project.wsgi:application`.
5. Click **Apply**.
6. Render runs `build.sh` (installs requirements, collects static files via WhiteNoise, runs migrations) and launches the application.

---

## 🧪 Automated Test Suite

Run all automated unit and integration tests:
```bash
python manage.py test
```

Test coverage includes:
- `test_user_registration_success`
- `test_user_registration_mismatched_passwords`
- `test_user_login_and_logout`
- `test_create_valid_expense`
- `test_reject_zero_or_negative_amount`
- `test_update_expense`
- `test_delete_expense`
- `test_user_cannot_view_others_expenses`
- `test_user_cannot_edit_others_expense`
- `test_user_cannot_delete_others_expense`
- `test_filter_by_category`
- `test_search_by_keyword`
- `test_csv_export`
- `test_budget_creation_and_status`
- `test_monthly_report_calculations`

---

## 🔒 Security & Data Integrity

- Passwords hashed using PBKDF2 with SHA256.
- All forms protected with Django CSRF tokens.
- Cross-user data isolation verified at view and database ORM layer.
- Currency amounts stored strictly with `DecimalField` (avoiding floating point inaccuracies).
- Environment secrets handled dynamically via environment variables (`SECRET_KEY`, `DATABASE_URL`, `DEBUG`).
