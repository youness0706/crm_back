from decimal import Decimal
from pyexpat.errors import messages
from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from .models import Student, StudentPayment, School, SchoolExpense,Event
from trainers.models import Staff
from django.db.models import Q  
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        # إذا هو أصلاً مسجّل الدخول نوجهوه مباشرة
        if request.user.is_superuser:
            return redirect('rawd_home')
        return redirect('students')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            try:
                staff = user.staff  # assuming Staff model has OneToOne with User
                if staff.role not in ['admin', 'rawd']:
                    messages.error(request, '❌ غير مصرح بالدخول')
                    return render(request, 'rawd_pages/login.html')
                login(request, user)
                messages.success(request, 'تم تسجيل الدخول بنجاح ✅')
                if user.is_superuser:
                    return redirect('rawd_home')
                else:
                    return redirect('rawd_home')
            except:
                messages.error(request, '❌ غير مصرح بالدخول')
                return render(request, 'rawd_pages/login.html')
        else:
            messages.error(request, '❌ اسم المستخدم أو كلمة المرور غير صحيحة')
            return render(request, 'rawd_pages/login.html')

    return render(request, 'rawd_pages/login.html')  # GET request


def logout_view(request):
    logout(request)
    messages.info(request, "تم تسجيل الخروج 👋")
    return redirect('rawd_login')  

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone

def add_staff(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = "rawd"
        is_admin = True if request.POST.get("is_admin") == "on" else False
        started = request.POST.get("started") or None
        salary = request.POST.get("salary") or 0
        datepay = request.POST.get("datepay") or timezone.now().date()
        email = request.POST.get("email") or None
        phone_number = request.POST.get("phone_number") or None

        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ اسم المستخدم موجود بالفعل")
        else:
            # Create user
            user = User.objects.create_user(username=username, password=password)
            
            # Create staff
            staff = Staff.objects.create(
                user=user,
                role=role,
                is_admin=is_admin,
                started=started,
                salary=salary,
                datepay=datepay,
                email=email,
                phone_number=phone_number,
            )
            staff.save()

            messages.success(request, "✅ تمت إضافة الموظف بنجاح")
            return redirect("rawd_info")  # أو أي صفحة أخرى

    return render(request, "rawd_pages/add_staff.html")


def rawd_info_page(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    rawd_info = School.objects.first()  # Assuming only one record

    staff_members = Staff.objects.filter(role__icontains="rawd") | Staff.objects.filter(role__icontains="admin")

    context = {
        "rawd_info": rawd_info,
        "staff_members": staff_members,
    }
    return render(request, "rawd_pages/rawd_info.html", context)

def rawd_home(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    user = request.user
    staff = get_object_or_404(Staff, user=user)
    print(staff.role)
    if staff.role == 'admin':
        pass
    elif staff.role == 'rawd':
        return redirect("students")
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models.functions import TruncMonth
    from django.db.models import Sum
    from decimal import Decimal

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # إحصائيات عامة
    total_students = Student.objects.count()
    new_students = Student.objects.filter(enrollment_date__gte=week_ago).count()

    total_income = StudentPayment.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_expenses = SchoolExpense.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_events = Event.objects.count()

    net_profit = total_income - total_expenses

    # 📊 بيانات شهرية (آخر 6 أشهر)
    from django.utils.timezone import now
    six_months_ago = today.replace(day=1) - timedelta(days=180)

    income_by_month = (
        StudentPayment.objects.filter(date__gte=six_months_ago)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    expenses_by_month = (
        SchoolExpense.objects.filter(date__gte=six_months_ago)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    # تجهيز البيانات للرسم
    labels = [entry["month"].strftime("%b %Y") for entry in income_by_month]
    income_data = [float(entry["total"]) for entry in income_by_month]
    expense_data = [
        float(next((e["total"] for e in expenses_by_month if e["month"] == entry["month"]), 0))
        for entry in income_by_month
    ]

    context = {
        "total_students": total_students,
        "new_students": new_students,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "total_events": total_events,
        "labels": labels,
        "income_data": income_data,
        "expense_data": expense_data,
    }
    return render(request, "rawd_pages/home.html", context)



def add_payment(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    if request.method == "POST":
        student_id = request.POST.get("student")
        payment_type = request.POST.get("type")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        payment_date = request.POST.get("payment_date")
        print("Payment Date:", payment_date)
        student = Student.objects.get(id=student_id)

        StudentPayment.objects.create(
            student=student,
            type=payment_type,
            amount=amount,
            description=description,
            date=payment_date if payment_date else None 
        ).save()

        return redirect("payments")  

    return render(request, "rawd_pages/addpayment.html")


# API للبحث عن الطلاب

def search_students(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    q = request.GET.get("q", "")
    students = Student.objects.filter(fname__icontains=q)[:20]  # أول 20 فقط
    results = [
        {"id": s.id, "text": f"{s.fname} {s.lname} - {s.grade}"}
        for s in students
    ]
    return JsonResponse({"results": results})

def rawd_students(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    students = Student.objects.all()

    # Filters
    fname = request.GET.get("fname")
    grade = request.GET.get("grade")
    gender = request.GET.get("gender")
    active = request.GET.get("active")

    if fname:
        students = students.filter(fname__icontains=fname)
    if grade and grade != "all":
        students = students.filter(grade=grade)
    if gender and gender != "all":
        students = students.filter(is_male=(gender == "male"))
    if active and active != "all":
        students = students.filter(is_active=(active == "1"))

    return render(request, "rawd_pages/students.html", {"students": students})


def remove_student(request, student_id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    student = get_object_or_404(Student, id=student_id)
    if student:
        student.delete()
        messages.success(request, "تمت إزالة الطالب بنجاح.")
    else:
        messages.error(request, "الطالب غير موجود.")
    return redirect('rawd_students')


def edit_student(request, student_id):  
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        student.fname = request.POST.get("fname")
        student.lname = request.POST.get("lname")
        student.grade = request.POST.get("grade")
        student.parent_name = request.POST.get("parent_name")
        student.parent_phone = request.POST.get("parent_phone")
        student.date_of_birth = request.POST.get("date_of_birth") or None
        student.is_male = request.POST.get("gender") == "ذكر"
        student.is_active = True if request.POST.get("is_active") == "on" else False
        if 'upload' in request.FILES:
            student.image = request.FILES['upload']
        student.save()

        return redirect("students")  # صفحة قائمة الطلاب

    context = {"student": student}
    return render(request, "rawd_pages/editstudent.html", context)


def rawd_student_profile(request, pk):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    student = get_object_or_404(Student, pk=pk)
    print(student.image.url)
    payments = StudentPayment.objects.filter(student=student).order_by('-date')

    # Handle payment form
    if request.method == "POST":
        form = StudentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.student = student
            payment.save()
            return redirect('rawd_student_profile', pk=student.pk)
    else:
        form = StudentPaymentForm()
    
    return render(request, 'rawd_pages/StuedentProfile.html', {
        'student': student,
        'payments': payments,
        'form': form
    })
from django import forms
from .models import StudentPayment


class StudentPaymentForm(forms.ModelForm):
    class Meta:
        model = StudentPayment
        fields = ['type', 'amount', 'description']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'المبلغ'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الوصف (اختياري)'}),
        }


def add_expense(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        date = request.POST.get("date")
        description = request.POST.get("description")

        SchoolExpense.objects.create(
            school=School.objects.first(), 
            title=title,
            amount=amount,
            date=date if date else None,
            description=description
        ).save()

        return redirect("rawd_expenses")  # صفحة عرض جميع المصاريف

    return render(request, "rawd_pages/addexpense.html")

from django.db.models import Sum


def rawd_expenses(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    expenses = SchoolExpense.objects.all().order_by("-date")
    total_amount = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    context = {
        "expenses": expenses,
        "total_amount": total_amount
    }
    return render(request, "rawd_pages/expenses.html", context)


def rawd_expense_delete(request, expense_id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    expense = get_object_or_404(SchoolExpense, id=expense_id)
    if expense:
        expense.delete()
        messages.success(request, "تمت إزالة المصروف بنجاح.")
    else:
        messages.error(request, "المصروف غير موجود.")
    return redirect('rawd_expenses')


def events_list(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    events = Event.objects.all().order_by("-date")
    context = {"events": events}
    return render(request, "rawd_pages/events_list.html", context)


# إضافة نشاط

def add_event(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    students = Student.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        event_type = request.POST.get("event_type")
        date = request.POST.get("date") or timezone.now().date()
        price = request.POST.get("price_per_participant") or 0
        expense = request.POST.get("total_expense") or 0
        participants = request.POST.getlist("participants")  # قائمة الطلاب المختارين

        event = Event.objects.create(
            title=title,
            description=description,
            event_type=event_type,
            date=date,
            price_per_participant=price,
            total_expense=expense
        )
        event.participants.set(participants)
        event.save()
        return redirect("events_list")

    context = {"students": students}
    return render(request, "rawd_pages/add_event.html", context)


def edit_event(request, event_id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    event = get_object_or_404(Event, id=event_id)
    students = Student.objects.all()

    if request.method == "POST":
        event.title = request.POST.get("title")
        event.event_type = request.POST.get("event_type")
        event.date = request.POST.get("date")
        event.price_per_participant = request.POST.get("price_per_participant") or 0
        event.total_expense = request.POST.get("total_expense") or 0
        event.description = request.POST.get("description")

        # تحديث المشاركين
        participants_ids = request.POST.getlist("participants")
        event.save()
        event.participants.set(participants_ids)

        return redirect("events_list")  # عدّلها حسب اسم url عندك

    return render(request, "rawd_pages/edit_event.html", {"event": event, "students": students})


def remove_event(request,id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    event = get_object_or_404(Event, id=id)
    if event:
        event.delete()
        messages.success(request, "تمت إزالة النشاط بنجاح.")
    else:
        messages.error(request, "النشاط غير موجود.")
    return redirect('events_list')



def rawd_financials(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    from django.utils.dateparse import parse_date
    from datetime import date

    # استرجاع الفترة من GET
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
    else:
        # افتراضي الشهر الحالي
        start_date = date.today().replace(day=1)
        end_date = date.today()

    # المدفوعات
    payments = StudentPayment.objects.filter(date__range=[start_date, end_date])
    total_payments = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)

    # المصاريف
    expenses = SchoolExpense.objects.filter(date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)

    # الأنشطة
    events = Event.objects.filter(date__range=[start_date, end_date])
    events_data = []
    total_events_income = Decimal(0)
    total_events_expenses = Decimal(0)

    for e in events:
        income = e.total_income()
        expense = e.total_expense
        profit = income - expense
        total_events_income += income
        total_events_expenses += expense
        events_data.append({
            "title": e.title,
            "income": income,
            "expense": expense,
            "profit": profit
        })

    
    rent_per_month = Decimal(School.objects.first().rent_amount)
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month + 1)
    rent_total = rent_per_month * months

    # صافي الربح
    net_profit = total_payments + total_events_income - (total_expenses + total_events_expenses + rent_total)

    context = {
        "payments": payments,
        "expenses": expenses,
        "events": events_data,
        "total_payments": total_payments,
        "total_expenses": total_expenses,
        "total_events_income": total_events_income,
        "total_events_expenses": total_events_expenses,
        "rent_total": rent_total,
        "net_profit": net_profit,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "rawd_pages/financials.html", context)


def add_student(request):
    
    if request.method != 'POST':
        return render(request, 'rawd_pages/addstudent.html')
    if 'upload' in request.FILES:
        upload = request.FILES['upload']
    else:
        upload = None
    fname = request.POST.get("first_name")
    lname = request.POST.get("last_name")
    grade = request.POST.get("grade")
    parent_name = request.POST.get("parent_name")
    parent_phone = request.POST.get("parent_phone")
    date_of_birth = request.POST.get("date_of_birth")
    enrollment_date = request.POST.get("enrollment_date")
    gender = request.POST.get("gender")

    # Create a new student instance
    checkrepeat = Student.objects.filter(fname=fname, lname=lname, grade=grade).exists()
    if not checkrepeat:
        student = Student.objects.create(
            school=School.objects.first(),  # Assuming a default school for simplicity
            fname=fname,
            lname= lname,
            grade=grade,
            parent_name=parent_name,
            parent_phone=parent_phone,
            date_of_birth=date_of_birth if date_of_birth else None,
            enrollment_date=enrollment_date if enrollment_date else None,
            is_male=gender == "male",
            is_active=True,
            image = upload
        )
        student.save()
        return redirect('students')
    else:
        return render(request, 'rawd_pages/addstudent.html', {'error': 'Student already exists.'})


def payments_page(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    payments = StudentPayment.objects.all().select_related("student")

    # Filters
    student_name = request.GET.get("student_name", "")
    payment_type = request.GET.get("type", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    if student_name:
        payments = payments.filter(
            Q(student__fname__icontains=student_name) | Q(student__lname__icontains=student_name)
        )
    if payment_type and payment_type != "all":
        payments = payments.filter(type=payment_type)
    if date_from:
        payments = payments.filter(date__gte=date_from)
    if date_to:
        payments = payments.filter(date__lte=date_to)

    context = {"payments": payments}
    return render(request, "rawd_pages/payments.html", context)


def edit_payment(request, payment_id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    payment = get_object_or_404(StudentPayment, id=payment_id)

    if request.method == "POST":
        payment.type = request.POST.get("type")
        payment.amount = request.POST.get("amount")
        payment.description = request.POST.get("description")
        payment.date = request.POST.get("date") or payment.date
        payment.save()
        return redirect("payments")

    context = {"payment": payment}
    return render(request, "rawd_pages/editpayment.html", context)


def remove_payment(request, payment_id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    payment = get_object_or_404(StudentPayment, id=payment_id)
    if payment:
        payment.delete()
        messages.success(request, "تمت إزالة الدفع بنجاح.")
    else:
        messages.error(request, "الدفع غير موجود.")
    return redirect('payments')



def edit_rawd_info(request):
    school = School.objects.first()  # نفترض أن عندك مدرسة وحدة فقط

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        established_year = request.POST.get("established_year")
        rent_amount = request.POST.get("rent_amount")

        if school:
            # تحديث المعلومات
            school.name = name
            school.address = address
            school.phone = phone
            school.email = email
            school.established_year = established_year or None
            school.rent_amount = rent_amount or 0
            school.save()
            messages.success(request, "✅ تم تحديث معلومات المدرسة بنجاح")
        else:
            # إذا ماكانش سجل
            School.objects.create(
                name=name,
                address=address,
                phone=phone,
                email=email,
                established_year=established_year or None,
                rent_amount=rent_amount or 0,
            )
            messages.success(request, "✅ تم إضافة معلومات المدرسة بنجاح")

        return redirect("rawd_info")  # صفحة عرض المعلومات

    

    context = {"school": school}
    return render(request, "rawd_pages/edit_rawd_info.html", context)


def remove_staff(request,id):
    staff = Staff.objects.get(id=id)
    staff.user.delete()  # حذف المستخدم المرتبط
    staff.delete()
    return redirect('rawd_info')

def addme(request):
    if request.method != 'POST':
        return render(request, 'rawd_pages/addstudent.html')
    if 'upload' in request.FILES:
        upload = request.FILES['upload']
    else:
        upload = None
    fname = request.POST.get("first_name")
    lname = request.POST.get("last_name")
    grade = request.POST.get("grade")
    parent_name = request.POST.get("parent_name")
    parent_phone = request.POST.get("parent_phone")
    date_of_birth = request.POST.get("date_of_birth")
    enrollment_date = request.POST.get("enrollment_date")
    gender = request.POST.get("gender")

    # Create a new student instance
    checkrepeat = Student.objects.filter(fname=fname, lname=lname, grade=grade).exists()
    if not checkrepeat:
        student = Student.objects.create(
            school=School.objects.first(),  # Assuming a default school for simplicity
            fname=fname,
            lname= lname,
            grade=grade,
            parent_name=parent_name,
            parent_phone=parent_phone,
            date_of_birth=date_of_birth if date_of_birth else None,
            enrollment_date=enrollment_date if enrollment_date else None,
            is_male=gender == "male",
            is_active=True,
            image = upload
        )
        student.save()
        return redirect('addmedone')
    else:
        return render(request, 'rawd_pages/addstudent.html', {'error': 'Student already exists.'})
def addmedone(request):
    return render(request, 'rawd_pages/addmedone.html')