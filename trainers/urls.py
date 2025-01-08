from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.Home, name='home'),
    #Trainees
    path('olders/<str:category>', views.trainees, name='trainees'),
    path('profile/<int:id>', views.trainee_profile, name='profile'),
    path('add_trainee', views.add_trainee, name='add_trainee'),
    path('add_women', views.add_women, name='add_women'),
    path('edit_trainee/<int:id>', views.edit_trainee, name='edit_trainee'),
    path("delete_trainer/<int:id>/", views.delete_trainer_view, name="delete_trainer"),
    #payments
    path('add_payment', views.add_payment, name='add_payment'),
    path('added_payment/', views.added_payment, name='added_payment'),
    path('payments_history/', views.payments_history, name='payments_history'),
    path('payments_del/<int:id>', views.payments_del, name='delete_payment'),
    path('payment_edit/<int:id>', views.payment_edit, name='edit_payment'),
    #JAWAZ
    path('add_article', views.add_article, name='add_article'),
    path('articles/<str:category>', views.articles, name='articles'),
    path('article/<int:id>', views.article_details, name='article_detail'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('edit_article/<int:id>', views.edit_article, name='edit_article'),
    #Financial
    path('finantial_status/',views.finantial_status,name='finantial_status'),
    path('add_expenses/',views.add_expenses,name='add_expenses'),
    path('add_payments/',views.add_payments,name='add_payments'),
    #Staff managing
    path("add_staff/",views.add_staff,name="add_staff") ,
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/edit/<int:staff_id>/', views.edit_staff, name='edit_staff'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('organization/edit/', views.edit_organization, name='edit_organization'),
    #login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    #emails
    path('emails/', views.emails, name='emails'),
    #success
    path('success/', views.success, name='success'),
    #DATA Download
    path('export_data/<str:category>', views.export_data, name='export_data'),

]
