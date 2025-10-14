from django.urls import path
from .rawd_views import *

urlpatterns = [
    # Auth URLs
    path('login/', login_view, name='rawd_login'),
    path('logout/', logout_view, name='rawd_logout'),
    
    # Home
    path('', rawd_home, name='rawd_home'),
    
    # Staff URLs
    path('add_staff/', add_staff, name='add_rawd_staff'),
    path('remove_staff/<int:id>/', remove_staff, name='remove_staff'),
    
    # School Info URLs
    path('rawd_info/', rawd_info_page, name='rawd_info'),
    path('edit_rawd_info/', edit_rawd_info, name='edit_rawd_info'),
    
    # Student URLs
    path('students/', rawd_students, name='students'),
    path('add_student/', add_student, name='add_student'),
    path('addme/', addme, name='addme'),
    path('addmedone/', addmedone, name='addmedone'),
    path('edit_student/<int:student_id>/', edit_student, name='edit_student'),
    path('remove_student/<int:student_id>/', remove_student, name='remove_student'),
    path('search_students/', search_students, name='search_students'),
    path('rawd_student_profile/<int:pk>/', rawd_student_profile, name='rawd_student_profile'),
    
    # Payment URLs
    path('add_payment/', add_payment, name='add_rawd_payment'),
    path('payments/', payments_page, name='payments'),
    path('edit_payment/<int:payment_id>/', edit_payment, name='edit_rawd_payment'),
    path('remove_payment/<int:payment_id>/', remove_payment, name='remove_rawd_payment'),
    path('payments/download-csv/', download_payments_csv, name='download_payments_csv'),
    path('payments/download-pdf/', download_payments_pdf, name='download_payments_pdf'),
    
    # Expense URLs
    path('add_expense/', add_expense, name='add_rawd_expense'),
    path('expenses/', rawd_expenses, name='rawd_expenses'),
    path('expense_delete/<int:expense_id>/', rawd_expense_delete, name='expense_delete'),
    
    # Event URLs
    path('add_event/', add_event, name='add_event'),
    path('events_list/', events_list, name='events_list'),
    path('edit_event/<int:event_id>/', edit_event, name='edit_event'),
    path('remove_event/<int:id>/', remove_event, name='remove_event'),
    
    # Financials URLs
    path('rawd_financials/', rawd_financials, name='rawd_financials'),
]