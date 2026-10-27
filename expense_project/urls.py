from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('expenses.urls')),
]

handler404 = 'expenses.views.custom_404_view'
handler500 = 'expenses.views.custom_500_view'
