from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class ExpenseCategory(models.TextChoices):
    FOOD = 'Food', 'Food'
    TRANSPORT = 'Transport', 'Transport'
    EDUCATION = 'Education', 'Education'
    SHOPPING = 'Shopping', 'Shopping'
    BILLS = 'Bills', 'Bills'
    HEALTHCARE = 'Healthcare', 'Healthcare'
    ENTERTAINMENT = 'Entertainment', 'Entertainment'
    TRAVEL = 'Travel', 'Travel'
    OTHER = 'Other', 'Other'


class PaymentMethod(models.TextChoices):
    CASH = 'Cash', 'Cash'
    CREDIT_CARD = 'Credit Card', 'Credit Card'
    DEBIT_CARD = 'Debit Card', 'Debit Card'
    UPI_WALLET = 'UPI / Digital Wallet', 'UPI / Digital Wallet'
    BANK_TRANSFER = 'Bank Transfer', 'Bank Transfer'
    OTHER = 'Other', 'Other'


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Amount spent (must be greater than 0)'
    )
    category = models.CharField(
        max_length=50,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.FOOD
    )
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    merchant = models.CharField(
        max_length=150,
        help_text='Merchant or short description (e.g. Walmart, Metro, Coffee)'
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.merchant} ({self.amount}) on {self.date}"


class MonthlyBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Monthly budget limit'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ('user', 'year', 'month')

    def __str__(self):
        return f"{self.user.username} Budget - {self.year}/{self.month:02d}: {self.amount}"
