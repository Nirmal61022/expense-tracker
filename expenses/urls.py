from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/add/', views.expense_create_view, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_update_view, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete_view, name='expense_delete'),
    path('report/', views.monthly_report_view, name='monthly_report'),
    path('budgets/', views.budget_manage_view, name='budget_manage'),
    path('budgets/<int:pk>/delete/', views.budget_delete_view, name='budget_delete'),
    path('export/csv/', views.export_csv_view, name='export_csv'),
]
