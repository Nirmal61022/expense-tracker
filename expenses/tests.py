from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Expense, MonthlyBudget, ExpenseCategory, PaymentMethod


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_success(self):
        response = self.client.post(reverse('expenses:register'), {
            'username': 'testuser1',
            'email': 'testuser1@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser1').exists())

    def test_user_registration_mismatched_passwords(self):
        response = self.client.post(reverse('expenses:register'), {
            'username': 'baduser',
            'email': 'baduser@example.com',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_user_login_and_logout(self):
        user = User.objects.create_user(username='loginuser', email='login@example.com', password='ValidPassword123!')
        login_res = self.client.post(reverse('expenses:login'), {
            'username': 'loginuser',
            'password': 'ValidPassword123!',
        })
        self.assertEqual(login_res.status_code, 302)
        self.assertEqual(login_res.url, reverse('expenses:dashboard'))

        logout_res = self.client.post(reverse('expenses:logout'))
        self.assertEqual(logout_res.status_code, 302)


class ExpenseCRUDAndValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='john', email='john@example.com', password='Password123!')
        self.client.login(username='john', password='Password123!')

    def test_create_valid_expense(self):
        response = self.client.post(reverse('expenses:expense_create'), {
            'amount': '45.50',
            'category': ExpenseCategory.FOOD,
            'date': '2026-10-25',
            'payment_method': PaymentMethod.CREDIT_CARD,
            'merchant': 'Grocery Mart',
            'notes': 'Weekly food supplies',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.count(), 1)
        exp = Expense.objects.first()
        self.assertEqual(exp.amount, Decimal('45.50'))
        self.assertEqual(exp.user, self.user)
        self.assertEqual(exp.merchant, 'Grocery Mart')

    def test_reject_zero_or_negative_amount(self):
        # Test zero amount
        res1 = self.client.post(reverse('expenses:expense_create'), {
            'amount': '0.00',
            'category': ExpenseCategory.FOOD,
            'date': '2026-10-25',
            'payment_method': PaymentMethod.CASH,
            'merchant': 'Free item',
        })
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)

        # Test negative amount
        res2 = self.client.post(reverse('expenses:expense_create'), {
            'amount': '-10.50',
            'category': ExpenseCategory.FOOD,
            'date': '2026-10-25',
            'payment_method': PaymentMethod.CASH,
            'merchant': 'Invalid negative',
        })
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)

    def test_update_expense(self):
        exp = Expense.objects.create(
            user=self.user,
            amount=Decimal('20.00'),
            category=ExpenseCategory.TRANSPORT,
            date=date(2026, 10, 20),
            payment_method=PaymentMethod.CASH,
            merchant='Taxi'
        )
        response = self.client.post(reverse('expenses:expense_update', kwargs={'pk': exp.pk}), {
            'amount': '25.00',
            'category': ExpenseCategory.TRANSPORT,
            'date': '2026-10-20',
            'payment_method': PaymentMethod.CREDIT_CARD,
            'merchant': 'Uber Ride',
            'notes': 'Late night ride',
        })
        self.assertEqual(response.status_code, 302)
        exp.refresh_from_db()
        self.assertEqual(exp.amount, Decimal('25.00'))
        self.assertEqual(exp.merchant, 'Uber Ride')
        self.assertEqual(exp.payment_method, PaymentMethod.CREDIT_CARD)

    def test_delete_expense(self):
        exp = Expense.objects.create(
            user=self.user,
            amount=Decimal('15.00'),
            category=ExpenseCategory.ENTERTAINMENT,
            date=date(2026, 10, 20),
            payment_method=PaymentMethod.CASH,
            merchant='Movie ticket'
        )
        self.assertEqual(Expense.objects.count(), 1)
        response = self.client.post(reverse('expenses:expense_delete', kwargs={'pk': exp.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.count(), 0)


class UserDataIsolationTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.user_a = User.objects.create_user(username='alice', email='alice@example.com', password='Password123!')
        self.client_a.login(username='alice', password='Password123!')

        self.client_b = Client()
        self.user_b = User.objects.create_user(username='bob', email='bob@example.com', password='Password123!')
        self.client_b.login(username='bob', password='Password123!')

        # Create Alice's expense
        self.expense_a = Expense.objects.create(
            user=self.user_a,
            amount=Decimal('100.00'),
            category=ExpenseCategory.SHOPPING,
            date=date(2026, 10, 20),
            payment_method=PaymentMethod.CREDIT_CARD,
            merchant='Alice Mall Purchase'
        )

        # Create Bob's expense
        self.expense_b = Expense.objects.create(
            user=self.user_b,
            amount=Decimal('200.00'),
            category=ExpenseCategory.ENTERTAINMENT,
            date=date(2026, 10, 20),
            payment_method=PaymentMethod.DEBIT_CARD,
            merchant='Bob Concert'
        )

    def test_user_cannot_view_others_expenses(self):
        # Alice views expense list
        response = self.client_a.get(reverse('expenses:expense_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Mall Purchase')
        self.assertNotContains(response, 'Bob Concert')

    def test_user_cannot_edit_others_expense(self):
        # Alice tries to edit Bob's expense
        response = self.client_a.post(
            reverse('expenses:expense_update', kwargs={'pk': self.expense_b.pk}),
            {
                'amount': '999.00',
                'category': ExpenseCategory.ENTERTAINMENT,
                'date': '2026-10-20',
                'payment_method': PaymentMethod.DEBIT_CARD,
                'merchant': 'Hacked Concert',
            }
        )
        self.assertEqual(response.status_code, 404)
        self.expense_b.refresh_from_db()
        self.assertEqual(self.expense_b.merchant, 'Bob Concert')
        self.assertEqual(self.expense_b.amount, Decimal('200.00'))

    def test_user_cannot_delete_others_expense(self):
        # Alice tries to delete Bob's expense
        response = self.client_a.post(reverse('expenses:expense_delete', kwargs={'pk': self.expense_b.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=self.expense_b.pk).exists())


class SearchFilterAndExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='sarah', email='sarah@example.com', password='Password123!')
        self.client.login(username='sarah', password='Password123!')

        Expense.objects.create(
            user=self.user,
            amount=Decimal('15.00'),
            category=ExpenseCategory.FOOD,
            date=date(2026, 10, 1),
            payment_method=PaymentMethod.CASH,
            merchant='Subway Sandwich',
            notes='Lunch'
        )
        Expense.objects.create(
            user=self.user,
            amount=Decimal('120.00'),
            category=ExpenseCategory.BILLS,
            date=date(2026, 10, 5),
            payment_method=PaymentMethod.BANK_TRANSFER,
            merchant='Electricity Bill',
            notes='Monthly power'
        )
        Expense.objects.create(
            user=self.user,
            amount=Decimal('45.00'),
            category=ExpenseCategory.FOOD,
            date=date(2026, 10, 15),
            payment_method=PaymentMethod.CREDIT_CARD,
            merchant='Dinner with Friends',
            notes='Italian restaurant'
        )

    def test_filter_by_category(self):
        response = self.client.get(reverse('expenses:expense_list') + '?category=Food')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subway Sandwich')
        self.assertContains(response, 'Dinner with Friends')
        self.assertNotContains(response, 'Electricity Bill')

    def test_search_by_keyword(self):
        response = self.client.get(reverse('expenses:expense_list') + '?q=Electricity')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Electricity Bill')
        self.assertNotContains(response, 'Subway Sandwich')

    def test_csv_export(self):
        response = self.client.get(reverse('expenses:export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Date,Merchant / Description,Category,Payment Method,Amount ($),Notes', content)
        self.assertIn('Electricity Bill', content)
        self.assertIn('Subway Sandwich', content)


class BudgetAndReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='mark', email='mark@example.com', password='Password123!')
        self.client.login(username='mark', password='Password123!')

        Expense.objects.create(
            user=self.user,
            amount=Decimal('300.00'),
            category=ExpenseCategory.FOOD,
            date=date(2026, 10, 10),
            payment_method=PaymentMethod.CREDIT_CARD,
            merchant='Supermarket'
        )
        Expense.objects.create(
            user=self.user,
            amount=Decimal('600.00'),
            category=ExpenseCategory.BILLS,
            date=date(2026, 10, 12),
            payment_method=PaymentMethod.BANK_TRANSFER,
            merchant='Apartment Rent'
        )

    def test_budget_creation_and_status(self):
        response = self.client.post(reverse('expenses:budget_manage'), {
            'year': 2026,
            'month': 10,
            'amount': '1000.00',
        })
        self.assertEqual(response.status_code, 302)
        budget = MonthlyBudget.objects.get(user=self.user, year=2026, month=10)
        self.assertEqual(budget.amount, Decimal('1000.00'))

        # Dashboard should reflect 90% spent (300+600=900 of 1000) -> warning state
        dash_res = self.client.get(reverse('expenses:dashboard'))
        self.assertEqual(dash_res.status_code, 200)
        self.assertEqual(dash_res.context['budget_status'], 'warning')
        self.assertEqual(dash_res.context['month_total'], Decimal('900.00'))

    def test_monthly_report_calculations(self):
        response = self.client.get(reverse('expenses:monthly_report') + '?year=2026&month=10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_spent'], Decimal('900.00'))
        self.assertEqual(response.context['total_count'], 2)
        self.assertEqual(response.context['top_category'], ExpenseCategory.BILLS)
