from django.contrib import admin
from student.models import *
# Register your models here.
admin.site.register(School)
admin.site.register(Student)
admin.site.register(SchoolExpense)
admin.site.register(Event)
admin.site.register(StudentPayment)
