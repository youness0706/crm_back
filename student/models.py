from django.db import models
from django.utils.timezone import now
import os
# Create your models here.
#Rawd Models

from django.db import models

class School(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المدرسة")
    address = models.CharField(max_length=255, verbose_name="العنوان", blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="الهاتف", blank=True, null=True)
    email = models.EmailField(verbose_name="البريد الإلكتروني", blank=True, null=True)
    established_year = models.PositiveIntegerField(verbose_name="سنة التأسيس", blank=True, null=True)
    rent_amount = models.FloatField(default=0, verbose_name="مبلغ الإيجار")

    def __str__(self):
        return self.name


class Teacher(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="teachers")
    name = models.CharField(max_length=200, verbose_name="اسم المعلم")
    subject = models.CharField(max_length=100, verbose_name="المادة")
    phone = models.CharField(max_length=20, verbose_name="الهاتف", blank=True, null=True)
    email = models.EmailField(verbose_name="البريد الإلكتروني", blank=True, null=True)
    hire_date = models.DateField(verbose_name="تاريخ التعيين", blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الراتب", default=0)

    def __str__(self):
        return f"{self.name} - {self.subject}"

def student_image_upload_to(instance, filename):
    """
    Custom function to generate the image upload path and filename.
    Images are stored in the directory `students/YYYY/MM/DD/` with the filename `first_last.ext`.
    """
    # Extract the file extension
    ext = filename.split('.')[-1]
    # Format the new filename
    filename = f"{instance.fname}_{instance.lname}.{ext}".lower()
    # Generate the upload path
    return os.path.join(f"students/{now().year}/{now().month:02}/{now().day:02}/", filename)

class Student(models.Model):
    grades = (
        ("1", "صف الصغار"),
        ("2", "الصف المتوسط"),
        ("3", "صف الكبار"),
    )
    image = models.ImageField(upload_to=student_image_upload_to, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="students")
    fname = models.CharField(max_length=200, verbose_name="اسم الشخصي")
    lname = models.CharField(max_length=200, verbose_name="اسم العائلة")
    is_male = models.BooleanField(default=True, verbose_name="ذكر/أنثى")
    date_of_birth = models.DateField(verbose_name="تاريخ الميلاد", blank=True, null=True)
    grade = models.CharField(max_length=50, verbose_name="المستوى/الصف", choices=grades)
    parent_name = models.CharField(max_length=200, verbose_name="اسم ولي الأمر", blank=True, null=True)
    parent_phone = models.CharField(max_length=20, verbose_name="هاتف ولي الأمر", blank=True, null=True)
    enrollment_date = models.DateField(verbose_name="تاريخ التسجيل", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="نشط/غير نشط")
    def __str__(self):
        return self.name


class SchoolExpense(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=200, verbose_name="اسم المصروف")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    date = models.DateField(verbose_name="التاريخ", blank=True, null=True)
    description = models.TextField(verbose_name="الوصف", blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.amount} درهم"

from django.db import models

class Event(models.Model):
    EVENT_TYPES = [
        ("trip", "Trip"),
        ("party", "Party"),
        ("tournament", "Tournament"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    date = models.DateField()
    price_per_participant = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # many-to-many relation with students
    participants = models.ManyToManyField("Student", related_name="events")

    total_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def total_income(self):
        return self.price_per_participant * self.participants.count()

    def profit(self):
        return self.total_income() - self.total_expense

    def __str__(self):
        return self.title


class StudentPayment(models.Model):
    paymentTypes = (
        ("monthly", "شهري"),
        ("annual", "سنوي"),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    type = models.CharField(max_length=100, verbose_name="نوع الدفع", choices=paymentTypes)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    date = models.DateField(verbose_name="التاريخ", blank=True, null=True)
    description = models.TextField(verbose_name="الوصف", blank=True, null=True)

    def __str__(self):
        return f"Payment of {self.amount} درهم for {self.student.name} on {self.date}"