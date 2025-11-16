from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.utils.timezone import now
import os, random




def image_upload_to(instance, filename):
    """
    Custom function to generate the image upload path and filename.
    Images are stored in the directory `trainees/YYYY/MM/DD/` with the filename `first_last.ext`.
    """
    # Extract the file extension
    ext = filename.split('.')[-1]
    # Format the new filename
    filename = f"{instance.first_name}_{instance.last_name}.{ext}".lower()
    # Generate the upload path
    return os.path.join(f"trainees/{now().year}/{now().month:02}/{now().day:02}/", filename)


class Trainer(models.Model):
    belts = (
        ("أبيض", "أبيض"),
        ("برتقالي ","برتقالي"),
        ("أصفر","أصفر"),
        ("أصفر مع شريط أخضر","أصفر مع شريط أخضر"),
        ("أخضر","أخضر"),
        ("أخضر مع شريط أزرق","أخضر مع شريط أزرق"),
        ("أزرق","أزرق"),
        ("أزرق مع شريط أحمر","أزرق مع شريط أحمر"),
        ("أحمر","أحمر"),
        ("أحمر مع شريط أسود","أحمر مع شريط أسود"),
        ("أسود","أسود"),
        
        )

    CatChoices = (
        ("small", "الصغار"),
        ("med", "فتيان"),
        ("big", "كبار"),
        ('women', 'نساء')
    )
    
    
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_day = models.DateField()
    phone = models.CharField(max_length=15, blank=True)
    phone_parent = models.IntegerField(blank=True)
    email = models.CharField(max_length=255)
    CIN = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=50, blank=True)
    male_female = models.CharField(max_length=11, choices=(('male', 'male'), ('female', 'female')))
    belt_degree = models.CharField(max_length=50, choices=belts, null=True)
    Degree = models.CharField(max_length=80, null=True)
    category = models.CharField(max_length=9, choices=CatChoices, default="small")
    tall = models.FloatField(blank=True)
    weight = models.FloatField(blank=True)
    started_day = models.DateField()
    is_active = models.BooleanField(default=True)

    # Use custom `upload_to` handler for `image`
    image = models.ImageField(upload_to=image_upload_to, blank=True)

    @property
    def age(self):
        if self.birth_day:
            # Calculate age by comparing years and adjusting for whether the birthday has occurred this year
            today = now().date()
            age = today.year - self.birth_day.year
            if (today.month, today.day) < (self.birth_day.month, self.birth_day.day):
                age -= 1
            return age
        return None

    @staticmethod
    def get_belt_choices():
        return Trainer.belts

    def __str__(self):
        return f"{self.first_name} {self.last_name} "

    @property
    def fone(self):
        if self.phone_parent == "phone_parent":
            self.phone_parent = self.phone
        return self.phone_parent
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['started_day']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['category', 'is_active']),  # Composite index
        ]
        ordering = ['-started_day']
   

class Payments(models.Model):
  CatChoices = (
    ("month", "شهرية"),
    ("subscription", "انخراط"),
    ("assurance", "التأمين"),
    ("jawaz", "جواز"),
  )
  trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
  paymentdate= models.DateField(default=timezone.now)
  paymentCategry  = models.CharField(default=True,choices=CatChoices, max_length=20)
  paymentAmount  = models.IntegerField(default=True)
  @staticmethod
  def get_catchoices():
        return Payments.CatChoices
  class Meta:
        indexes = [
            models.Index(fields=['trainer', 'paymentCategry', '-paymentdate']),
            models.Index(fields=['paymentdate']),
        ]

class Article(models.Model):
    choices = (('local','محلي'),
               ('reigion','جهوي'),
               ('national','وطني'),
               ) 
    cts = (('League','بطولة'),
           ('training','تدريب'),
           ('dawri','دوري'),
           ('test','امتحان'),
           ('out','خرجة'),
           ('other','اخرى'),
           )
    date    = models.DateField(default=timezone.now)
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=500,default="اركانة نجوم اركانة")
    content = RichTextField()  
    trainees = models.ManyToManyField(Trainer,blank=True)
    category = models.CharField(choices=cts,max_length=30)
    area = models.CharField(choices=choices,max_length=30)
    costs = models.FloatField(blank=True)
    participetion_price = models.FloatField(blank=True)
    @property
    def profit(self):
        if self.costs is not None and self.participetion_price is not None:
            return self.participetion_price*self.trainees.count()
        return None
    @property
    def net_profit(self):
        if self.costs is not None and self.participetion_price is not None:
            return self.participetion_price*self.trainees.count()-self.costs
        return None
    @staticmethod
    def get_area_choices():
        return Article.choices
    @staticmethod
    def get_categories():
        return Article.cts
    

class Costs(models.Model):
  cost = models.CharField(max_length=100)
  desc = models.TextField(blank=True)
  amount = models.FloatField()
  date = models.DateTimeField()
  is_allways = models.BooleanField(default=False)

class Addedpay(models.Model):
  title = models.CharField(max_length=100)
  desc = models.TextField(blank=True)
  amount = models.FloatField()
  date = models.DateTimeField()
  


class OrganizationInfo(models.Model):
    name = models.CharField(max_length=255, default='اسم الجمعية')
    description = models.TextField(blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    rent_amount = models.FloatField(default=0)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    datepay = models.DateField(blank=True)

    def __str__(self):
        return self.name
    
class Staff(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  role = models.CharField(max_length=100)
  is_admin = models.BooleanField(default=False)
  started = models.DateField(blank=True)
  salary = models.FloatField(default=0)
  datepay=models.DateField(blank=True,default=timezone.now)
  email = models.EmailField(blank=True,null=True)
  phone_number = models.CharField(blank=True,max_length=15)

class Emailed(models.Model):
   user = models.ForeignKey(Trainer,on_delete=models.CASCADE)
   datetime = models.DateField(default=timezone.now)
   email = models.CharField(max_length=3000, blank=True)
   category = models.CharField(max_length=300,default='monthly')

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