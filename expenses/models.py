from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


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


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('getting_started', 'Getting Started'),
        ('expenses', 'Expenses & Transactions'),
        ('budgets', 'Budgets & Limits'),
        ('reports', 'Reports & Analytics'),
        ('account', 'Account & Security'),
        ('troubleshooting', 'Troubleshooting'),
    ]

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='getting_started')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class ErrorCode(models.Model):
    CATEGORY_CHOICES = [
        ('client', 'Client Error (4xx)'),
        ('server', 'Server Error (5xx)'),
        ('application', 'Application Error (EXP-xxx)'),
    ]

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField()
    solution = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='client')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    ticket_id = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='support_tickets')
    name = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    source = models.CharField(max_length=50, default='ai_assistant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            # Generate clean human-readable ticket ID like TCK-84729
            self.ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ticket_id}] {self.subject} ({self.status})"
