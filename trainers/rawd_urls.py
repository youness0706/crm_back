from django.urls import path,include
from .rawd_views import *

urlpatterns = [

    #RAWD naja7
    path('', rawd_home, name='rawd_home'),
    path('students/', rawd_students, name='students'),
    path('rawd_student_profile/<int:pk>/', rawd_student_profile, name='rawd_student_profile'),
    path('rawd_expenses/', rawd_expenses, name='rawd_expenses'),
    path('rawd_financials/', rawd_financials, name='rawd_financials'),
    path('add_student/', add_student, name='add_student'),
    path('add_payment/', add_payment, name='add_payment'),
    path('search_students/', search_students, name='search_students'),
    path('payments/', payments_page, name='payments'),
    path('edit_payment/<int:payment_id>/', edit_payment, name='edit_payment'),
    path('remove_payment/<int:payment_id>/', remove_payment, name='remove_payment'),
    path('remove_student/<int:student_id>/', remove_student, name='remove_student'),
    path('edit_student/<int:student_id>/', edit_student, name='edit_student'),
    path('add_expense/', add_expense, name='add_expense'),
    path('expenses/', rawd_expenses, name='expenses'),
    path('expense_delete/<int:expense_id>/', rawd_expense_delete, name='expense_delete'),
    path('add_event/', add_event, name='add_event'),
    path('events_list/', events_list, name='events_list'),
    path('edit_event/<int:event_id>/', edit_event, name='edit_event'),
    path('remove_event/<int:id>/', remove_event, name='remove_event'),
    path('login/', login_view, name='rawd_login'),
    path('logout/',logout_view,name='rawd_logout'),
    path('add_staff/', add_staff, name='add_staff'),
    path('rawd_info/', rawd_info_page, name='rawd_info'),
    path('edit_rawd_info/', edit_rawd_info, name='edit_rawd_info'),
    path('remove_staff/<int:id>/', remove_staff, name='remove_staff'),
    path('addme/', addme, name='addme'),
    path('addmedone/', addmedone, name='addmedone'),
]