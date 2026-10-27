from django.contrib import admin
from .models import Expense, MonthlyBudget


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'merchant', 'amount', 'category', 'payment_method', 'date', 'created_at')
    list_filter = ('category', 'payment_method', 'date', 'user')
    search_fields = ('merchant', 'notes', 'user__username')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'month', 'amount', 'created_at')
    list_filter = ('year', 'month', 'user')
    search_fields = ('user__username',)
