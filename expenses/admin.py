from django.contrib import admin
from .models import Expense, MonthlyBudget, FAQ, ErrorCode, SupportTicket


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


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('code', 'title', 'description', 'solution')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'subject', 'email', 'status', 'priority', 'source', 'created_at')
    list_filter = ('status', 'priority', 'source')
    search_fields = ('ticket_id', 'subject', 'email', 'description')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
