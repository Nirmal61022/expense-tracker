from django.db import migrations


def seed_data(apps, schema_editor):
    FAQ = apps.get_model('expenses', 'FAQ')
    ErrorCode = apps.get_model('expenses', 'ErrorCode')

    faqs = [
        {
            'question': 'How do I add a new expense in ExpenseFlow?',
            'answer': 'Navigate to the "Add Expense" button in the sidebar or top navigation. Enter the monetary amount (must be positive), choose an expense category (e.g. Food, Transport, Bills), enter the date, select the payment method, and specify the merchant or description. Click "Save Expense" to log it.',
            'category': 'getting_started',
            'order': 1,
        },
        {
            'question': 'How does the Monthly Budget Planner work?',
            'answer': 'Go to the "Budget Planner" page. Choose the target month and year, enter your spending limit, and click "Save Budget Limit". ExpenseFlow automatically sums all expenses logged in that month and computes your remaining balance and utilization percentage.',
            'category': 'budgets',
            'order': 2,
        },
        {
            'question': 'What happens when I approach or exceed my monthly budget?',
            'answer': 'ExpenseFlow features a dynamic tri-color warning alert system: when you have utilized under 80% of your budget, the bar displays green (Safe). Between 80% and 100%, an amber caution alert is displayed. If your spending exceeds 100%, a prominent red danger banner notifies you with the exact over-budget amount.',
            'category': 'budgets',
            'order': 3,
        },
        {
            'question': 'How can I filter and sort my expenses?',
            'answer': 'On the "All Expenses" page, use the multi-criteria filter toolbar. You can search by merchant keyword or notes, filter by category or payment method, specify date ranges (Date From / Date To), set amount thresholds, and sort by newest, oldest, highest amount, or lowest amount.',
            'category': 'expenses',
            'order': 4,
        },
        {
            'question': 'Can I export my financial data to CSV or Excel?',
            'answer': 'Yes! On the "All Expenses" page, click the "Export CSV" button. It exports your expense records into a standard spreadsheet CSV file. Any active search filters or date ranges you have selected are preserved during export.',
            'category': 'reports',
            'order': 5,
        },
        {
            'question': 'How is my financial data protected and isolated?',
            'answer': 'ExpenseFlow enforces strict multi-tenant data isolation. Every expense record and budget is tied to your authenticated user ID. It is impossible for another user to view, edit, or delete your financial data, backed by database ORM query constraints and automated isolation tests.',
            'category': 'account',
            'order': 6,
        },
        {
            'question': 'What categories and payment methods are supported?',
            'answer': 'ExpenseFlow supports 9 primary categories: Food, Transport, Education, Shopping, Bills, Healthcare, Entertainment, Travel, and Other. Supported payment methods include Cash, Credit Card, Debit Card, UPI / Digital Wallet, Bank Transfer, and Other.',
            'category': 'expenses',
            'order': 7,
        },
        {
            'question': 'How do I interpret the Monthly Report analytics?',
            'answer': 'Visit the "Monthly Reports" page to inspect total expenditure for any selected month, active daily averages, peak spending day, and top spending category. The page also features a category doughnut distribution chart, a daily timeline chart, and a percentage breakdown table.',
            'category': 'reports',
            'order': 8,
        },
        {
            'question': 'Can I edit or delete an existing expense?',
            'answer': 'Yes. Next to any transaction on the Dashboard or All Expenses list, click the pencil icon to edit or the trash icon to delete. A safety confirmation modal prevents accidental deletions.',
            'category': 'expenses',
            'order': 9,
        },
        {
            'question': 'How does the AI Assistant help me?',
            'answer': 'The floating AI chat assistant in the bottom-right corner is accessible on every page. It can explain error codes, guide you through app features using the FAQ database, and automatically open support tickets when you need technical assistance.',
            'category': 'troubleshooting',
            'order': 10,
        },
        {
            'question': 'What should I do if I encounter an error code?',
            'answer': 'Ask our AI Assistant in the chat widget (e.g. "What is error 404?" or "Explain 500"), or browse the Error Codes directory on the FAQ page for descriptions, root causes, and recommended solutions.',
            'category': 'troubleshooting',
            'order': 11,
        },
        {
            'question': 'How do I open a support ticket if something goes wrong?',
            'answer': 'You can submit a ticket via the Support page (/support/) or ask the AI assistant directly in the chat widget (e.g., "Create a support ticket for my issue"). The assistant creates the ticket in SQL and gives you a tracking ID.',
            'category': 'troubleshooting',
            'order': 12,
        },
    ]

    for item in faqs:
        FAQ.objects.get_or_create(question=item['question'], defaults=item)

    error_codes = [
        {
            'code': '400',
            'title': 'Bad Request',
            'category': 'client',
            'description': 'The server cannot process the request due to malformed request syntax, missing required parameters, or invalid payload validation.',
            'solution': 'Check your form input fields. Ensure that amounts are valid positive decimal numbers (e.g. 15.50) and dates follow the standard YYYY-MM-DD format.'
        },
        {
            'code': '401',
            'title': 'Unauthorized',
            'category': 'client',
            'description': 'The requested resource requires user authentication. You are currently not logged in or your session has expired.',
            'solution': 'Please log in with your account credentials. If you do not have an account, register for a new account on the Sign Up page.'
        },
        {
            'code': '403',
            'title': 'Forbidden',
            'category': 'client',
            'description': 'The server understood your request, but refuses to authorize it. You do not have permission to view or manipulate this resource.',
            'solution': 'Make sure you are not attempting to access, edit, or delete another user\'s private financial records. Cross-account access is strictly blocked.'
        },
        {
            'code': '404',
            'title': 'Not Found',
            'category': 'client',
            'description': 'The requested web page, endpoint, or expense resource could not be found on the server.',
            'solution': 'Check the URL spelling. Use the navigation sidebar or click "Ask the Assistant" on the 404 page for quick assistance returning to the dashboard.'
        },
        {
            'code': '429',
            'title': 'Too Many Requests',
            'category': 'client',
            'description': 'Rate limit exceeded. The client has sent too many requests in a given amount of time to prevent abuse and denial of service.',
            'solution': 'Wait 30 to 60 seconds before refreshing or submitting more form data. Reduce rapid consecutive submissions.'
        },
        {
            'code': '500',
            'title': 'Internal Server Error',
            'category': 'server',
            'description': 'The server encountered an unexpected error while processing your request and was unable to complete the operation.',
            'solution': 'Refresh the page or click "Ask the Assistant" to immediately file a support ticket so our engineering team can investigate the issue.'
        },
        {
            'code': '503',
            'title': 'Service Unavailable',
            'category': 'server',
            'description': 'The server is temporarily unable to handle the request due to maintenance, high load, or a transient infrastructure outage.',
            'solution': 'Wait a few moments and refresh. Check our /health/ status page to confirm that database and application services are operational.'
        },
        {
            'code': 'EXP-4001',
            'title': 'Budget Limit Overrun',
            'category': 'application',
            'description': 'Site-specific application error: The expense you attempted to log causes your total monthly expenditure to surpass your allocated spending limit.',
            'solution': 'Review your spending limits in the Budget Planner (/budgets/) or adjust your budget target to accommodate this expenditure.'
        },
        {
            'code': 'EXP-4002',
            'title': 'Negative or Zero Ledger Amount',
            'category': 'application',
            'description': 'Site-specific application error: An expense was submitted with a non-positive monetary amount ($0.00 or negative).',
            'solution': 'All expense transactions must be positive values greater than $0.00. For credits or refunds, log an explanatory note with a positive value.'
        },
    ]

    for item in error_codes:
        ErrorCode.objects.get_or_create(code=item['code'], defaults=item)


def reverse_seed(apps, schema_editor):
    FAQ = apps.get_model('expenses', 'FAQ')
    ErrorCode = apps.get_model('expenses', 'ErrorCode')
    FAQ.objects.all().delete()
    ErrorCode.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_errorcode_faq_supportticket'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_seed),
    ]
