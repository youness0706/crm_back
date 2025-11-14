from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django import forms
from datetime import datetime, timedelta, date
from django.utils.dateparse import parse_date
import csv
import os
from io import BytesIO

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# Arabic text reshaping
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

from .models import Student, StudentPayment, School, SchoolExpense, Event
from trainers.models import Staff


# ======================== AUTH VIEWS ========================

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('rawd_home')
        return redirect('students')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            try:
                staff = user.staff
                if staff.role not in ['admin', 'rawd']:
                    messages.error(request, 'غير مصرح بالدخول')
                    return render(request, 'rawd_pages/login.html')
                login(request, user)
                messages.success(request, 'تم تسجيل الدخول بنجاح')
                return redirect('rawd_home')
            except:
                messages.error(request, 'غير مصرح بالدخول')
                return render(request, 'rawd_pages/login.html')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
            return render(request, 'rawd_pages/login.html')

    return render(request, 'rawd_pages/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "تم تسجيل الخروج")
    return redirect('rawd_login')


# ======================== STAFF VIEWS ========================

def add_staff(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        is_admin = request.POST.get("is_admin") == "on"
        started = request.POST.get("started") or None
        salary = request.POST.get("salary") or 0
        datepay = request.POST.get("datepay") or timezone.now().date()
        email = request.POST.get("email") or None
        phone_number = request.POST.get("phone_number") or None

        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم موجود بالفعل")
        else:
            user = User.objects.create_user(username=username, password=password)
            Staff.objects.create(
                user=user,
                role="rawd",
                is_admin=is_admin,
                started=started,
                salary=salary,
                datepay=datepay,
                email=email,
                phone_number=phone_number,
            )
            messages.success(request, "تمت إضافة الموظف بنجاح")
            return redirect("rawd_info")

    return render(request, "rawd_pages/add_staff.html")


def remove_staff(request, id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    staff = get_object_or_404(Staff, id=id)
    staff.user.delete()
    staff.delete()
    return redirect('rawd_info')


# ======================== SCHOOL INFO VIEWS ========================

def rawd_info_page(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    rawd_info = School.objects.first()
    staff_members = Staff.objects.filter(role__icontains="rawd") | Staff.objects.filter(role__icontains="admin")

    context = {
        "rawd_info": rawd_info,
        "staff_members": staff_members,
    }
    return render(request, "rawd_pages/rawd_info.html", context)


def edit_rawd_info(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    school = School.objects.first()

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        established_year = request.POST.get("established_year")
        rent_amount = request.POST.get("rent_amount")

        if school:
            school.name = name
            school.address = address
            school.phone = phone
            school.email = email
            school.established_year = established_year or None
            school.rent_amount = rent_amount or 0
            school.save()
            messages.success(request, "تم تحديث معلومات المدرسة بنجاح")
        else:
            School.objects.create(
                name=name,
                address=address,
                phone=phone,
                email=email,
                established_year=established_year or None,
                rent_amount=rent_amount or 0,
            )
            messages.success(request, "تمت إضافة معلومات المدرسة بنجاح")

        return redirect("rawd_info")

    context = {"school": school}
    return render(request, "rawd_pages/edit_rawd_info.html", context)


# ======================== HOME VIEW ========================

def rawd_home(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    user = request.user
    staff = get_object_or_404(Staff, user=user)
    
    if staff.role == 'rawd':
        return redirect("students")

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    six_months_ago = today.replace(day=1) - timedelta(days=180)

    # Statistics - exclude None dates
    total_students = Student.objects.count()
    new_students = Student.objects.filter(enrollment_date__gte=week_ago).count()
    total_income = StudentPayment.objects.filter(date__isnull=False).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_expenses = SchoolExpense.objects.filter(date__isnull=False).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_events = Event.objects.count()
    net_profit = total_income - total_expenses

    # Monthly data (last 6 months) - exclude None dates
    from django.db.models.functions import TruncMonth
    
    income_by_month = (
        StudentPayment.objects.filter(date__isnull=False, date__gte=six_months_ago)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    expenses_by_month = (
        SchoolExpense.objects.filter(date__isnull=False, date__gte=six_months_ago)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    labels = [entry["month"].strftime("%b %Y") for entry in income_by_month] if income_by_month else []
    income_data = [float(entry["total"]) for entry in income_by_month] if income_by_month else []
    expense_data = [
        float(next((e["total"] for e in expenses_by_month if e["month"] == entry["month"]), 0))
        for entry in income_by_month
    ] if income_by_month else []

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


# ======================== STUDENT VIEWS ========================

def rawd_students(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    students = Student.objects.all()

    fname = request.GET.get("fname", "").strip()
    grade = request.GET.get("grade", "").strip()
    gender = request.GET.get("gender", "").strip()
    active = request.GET.get("active", "").strip()

    if fname:
        students = students.filter(fname__icontains=fname)
    if grade and grade != "all":
        students = students.filter(grade=grade)
    if gender and gender != "all":
        students = students.filter(is_male=(gender == "male"))
    if active and active != "all":
        students = students.filter(is_active=(active == "1"))

    return render(request, "rawd_pages/students.html", {"students": students})


def add_student(request):
    if request.method != 'POST':
        return render(request, 'rawd_pages/addstudent.html')
    
    fname = request.POST.get("first_name")
    lname = request.POST.get("last_name")
    grade = request.POST.get("grade")
    parent_name = request.POST.get("parent_name")
    parent_phone = request.POST.get("parent_phone")
    date_of_birth = request.POST.get("date_of_birth")
    enrollment_date = request.POST.get("enrollment_date")
    gender = request.POST.get("gender")
    upload = request.FILES.get('upload', None)

    # Check if student already exists
    if Student.objects.filter(fname=fname, lname=lname, grade=grade).exists():
        return render(request, 'rawd_pages/addstudent.html', {'error': 'الطالب موجود بالفعل'})

    Student.objects.create(
        school=School.objects.first(),
        fname=fname,
        lname=lname,
        grade=grade,
        parent_name=parent_name,
        parent_phone=parent_phone,
        date_of_birth=date_of_birth or None,
        enrollment_date=enrollment_date or None,
        is_male=gender == "male",
        is_active=True,
        image=upload
    )
    return redirect('students')


def addme(request):
    if request.method != 'POST':
        return render(request, 'rawd_pages/addstudent.html')
    
    fname = request.POST.get("first_name")
    lname = request.POST.get("last_name")
    grade = request.POST.get("grade")
    parent_name = request.POST.get("parent_name")
    parent_phone = request.POST.get("parent_phone")
    date_of_birth = request.POST.get("date_of_birth")
    enrollment_date = request.POST.get("enrollment_date")
    gender = request.POST.get("gender")
    upload = request.FILES.get('upload', None)

    if Student.objects.filter(fname=fname, lname=lname, grade=grade).exists():
        return render(request, 'rawd_pages/addstudent.html', {'error': 'الطالب موجود بالفعل'})

    Student.objects.create(
        school=School.objects.first(),
        fname=fname,
        lname=lname,
        grade=grade,
        parent_name=parent_name,
        parent_phone=parent_phone,
        date_of_birth=date_of_birth or None,
        enrollment_date=enrollment_date or None,
        is_male=gender == "male",
        is_active=True,
        image=upload
    )
    return redirect('addmedone')


def addmedone(request):
    return render(request, 'rawd_pages/addmedone.html')


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
        student.is_active = request.POST.get("is_active") == "on"
        if 'upload' in request.FILES:
            student.image = request.FILES['upload']
        student.save()
        return redirect("students")

    context = {"student": student}
    return render(request, "rawd_pages/editstudent.html", context)


def remove_student(request, student_id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    student = get_object_or_404(Student, id=student_id)
    student.delete()
    messages.success(request, "تمت إزالة الطالب بنجاح")
    return redirect('students')


def search_students(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    q = request.GET.get("q", "")
    students = Student.objects.filter(fname__icontains=q)[:20]
    results = [
        {"id": s.id, "text": f"{s.fname} {s.lname} - {s.grade}"}
        for s in students
    ]
    return JsonResponse({"results": results})


def rawd_student_profile(request, pk):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    student = get_object_or_404(Student, pk=pk)
    payments = StudentPayment.objects.filter(student=student).order_by('-date')

    if request.method == "POST":
        form = StudentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.student = student
            payment.save()
            return redirect('rawd_student_profile', pk=student.pk)
    else:
        form = StudentPaymentForm()

    return render(request, 'rawd_pages/stuedentprofile.html', {
        'student': student,
        'payments': payments,
        'form': form
    })


# ======================== PAYMENT VIEWS ========================

class StudentPaymentForm(forms.ModelForm):
    class Meta:
        model = StudentPayment
        fields = ['type', 'amount', 'description']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'المبلغ'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'الوصف (اختياري)'}),
        }


def add_payment(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    if request.method == "POST":
        student_id = request.POST.get("student")
        payment_type = request.POST.get("type")
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        payment_date = request.POST.get("payment_date")

        student = Student.objects.get(id=student_id)
        StudentPayment.objects.create(
            student=student,
            type=payment_type,
            amount=amount,
            description=description,
            date=payment_date or None
        )
        return redirect("payments")

    return render(request, "rawd_pages/addpayment.html")


def payments_page(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    # Exclude payments with None dates for ordering
    payments = StudentPayment.objects.filter(date__isnull=False).select_related("student").order_by("-date")

    student_name = request.GET.get("student_name", "").strip()
    payment_type = request.GET.get("type", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

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

    total_amount = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)

    context = {
        "payments": payments,
        "total_amount": total_amount,
        "student_name": student_name,
        "payment_type": payment_type,
        "date_from": date_from,
        "date_to": date_to,
    }
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
    payment.delete()
    messages.success(request, "تمت إزالة الدفع بنجاح")
    return redirect('payments')


def download_payments_csv(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    # Exclude payments with None dates
    payments = StudentPayment.objects.filter(date__isnull=False).select_related("student").order_by("-date")
    
    student_name = request.GET.get("student_name", "").strip()
    payment_type = request.GET.get("type", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

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

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="payments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['#', 'اسم الطالب', 'النوع', 'المبلغ', 'التاريخ', 'الوصف'])
    
    for idx, payment in enumerate(payments, 1):
        payment_type_label = 'شهري' if payment.type == 'monthly' else 'سنوي'
        writer.writerow([
            idx,
            f'{payment.student.fname} {payment.student.lname}',
            payment_type_label,
            f'{payment.amount}',
            payment.date.strftime('%Y-%m-%d') if payment.date else '-',
            payment.description or '-'
        ])
    
    total = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)
    writer.writerow([])
    writer.writerow(['الإجمالي', '', '', f'{total}', '', ''])
    
    return response


def arabic_text(text):
    """Helper function to reshape Arabic text for PDF"""
    if ARABIC_SUPPORT and text:
        try:
            reshaped = reshape(text)
            return get_display(reshaped)
        except:
            return text
    return text


def download_payments_pdf(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    # Check if Arabic support libraries are installed
    if not ARABIC_SUPPORT:
        messages.error(request, 'خطأ: المكتبات المطلوبة غير مثبتة. قم بتثبيت: pip install arabic-reshaper python-bidi')
        return redirect('payments')
    
    payments = StudentPayment.objects.filter(date__isnull=False).select_related("student").order_by("-date")
    
    student_name = request.GET.get("student_name", "").strip()
    payment_type = request.GET.get("type", "").strip()
    date_from_raw = request.GET.get("date_from", "").strip()
    date_to_raw = request.GET.get("date_to", "").strip()

    # Convert to proper date objects or None
    date_from = parse_date(date_from_raw) if date_from_raw else None
    date_to = parse_date(date_to_raw) if date_to_raw else None

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

    buffer = BytesIO()
    
    # Create PDF with landscape orientation for better table fit
    pdf = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=1*cm, 
        leftMargin=1*cm,
        topMargin=1.5*cm, 
        bottomMargin=1.5*cm
    )
    
    # Register Arabic font - NotoSansArabic
    import os
    font_name = 'NotoSansArabic'
    try:
        # Get the path to the font file (same directory as views.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_dir, 'NotoSansArabic.ttf')
    
        # Register the font
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception as e:
        # Fallback to Helvetica if font file not found
        font_name = 'Helvetica'
        messages.warning(request, f'تحذير: لم يتم العثور على الخط العربي. خطأ: {str(e)}')
    
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'ArabicTitle',
        fontName=font_name,
        fontSize=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12
    )
    
    title_text = arabic_text('سجل الدفعات')
    elements.append(Paragraph(title_text, title_style))
    
    # Date range
    date_from_str = date_from.strftime('%Y-%m-%d') if date_from else 'البداية'
    date_to_str = date_to.strftime('%Y-%m-%d') if date_to else 'النهاية'
    info_text = arabic_text(f'الفترة: من {date_from_str} إلى {date_to_str}')
    
    info_style = ParagraphStyle(
        'ArabicInfo', 
        fontName=font_name, 
        fontSize=14, 
        alignment=TA_CENTER,
        spaceAfter=20
    )
    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Table data - Headers
    data = [[
        arabic_text('#'),
        arabic_text('اسم الطالب'),
        arabic_text('النوع'),
        arabic_text('المبلغ'),
        arabic_text('التاريخ'),
        arabic_text('الوصف')
    ]]
    
    total_amount = Decimal(0)
    for idx, payment in enumerate(payments, 1):
        payment_type_label = 'شهري' if payment.type == 'monthly' else 'سنوي'
        student_name_raw = f"{payment.student.fname or ''} {payment.student.lname or ''}".strip() or "-"
        amount = Decimal(payment.amount or 0)
        date_str = payment.date.strftime('%Y-%m-%d') if payment.date else "-"
        description = payment.description or "-"
        
        total_amount += amount
        
        data.append([
            str(idx),
            arabic_text(student_name_raw),
            arabic_text(payment_type_label),
            arabic_text(f'{amount} درهم'),
            date_str,
            arabic_text(description)
        ])
    
    # Total row
    data.append([
        '',
        '',
        arabic_text('الإجمالي'),
        arabic_text(f'{total_amount} درهم'),
        '',
        ''
    ])
    
    # Create table with appropriate column widths
    col_widths = [2*cm, 5*cm, 3*cm, 4*cm, 4*cm, 7*cm]
    table = Table(data, colWidths=col_widths)
    
    # Style the table
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        
        # Total row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d9d9d9')),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('FONTNAME', (0, -1), (-1, -1), font_name),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Footer
    elements.append(Spacer(1, 0.5*cm))
    footer_text = arabic_text(f'تم الإنشاء: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    footer_style = ParagraphStyle(
        'Footer',
        fontName=font_name,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    try:
        pdf.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"خطأ في إنشاء PDF: {str(e)}")
        return redirect('payments')


# ======================== EXPENSE VIEWS ========================

def add_expense(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        exp_date = request.POST.get("date")
        description = request.POST.get("description")

        SchoolExpense.objects.create(
            school=School.objects.first(),
            title=title,
            amount=amount,
            date=exp_date or None,
            description=description
        )
        return redirect("rawd_expenses")

    return render(request, "rawd_pages/addexpense.html")


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
    expense.delete()
    messages.success(request, "تمت إزالة المصروف بنجاح")
    return redirect('rawd_expenses')


# ======================== EVENT VIEWS ========================

def add_event(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    students = Student.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        event_type = request.POST.get("event_type")
        event_date = request.POST.get("date") or timezone.now().date()
        price = request.POST.get("price_per_participant") or 0
        expense = request.POST.get("total_expense") or 0
        participants = request.POST.getlist("participants")

        event = Event.objects.create(
            title=title,
            description=description,
            event_type=event_type,
            date=event_date,
            price_per_participant=price,
            total_expense=expense
        )
        event.participants.set(participants)
        return redirect("events_list")

    context = {"students": students}
    return render(request, "rawd_pages/add_event.html", context)


def events_list(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    events = Event.objects.all().order_by("-date")
    context = {"events": events}
    return render(request, "rawd_pages/events_list.html", context)


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
        event.save()

        participants_ids = request.POST.getlist("participants")
        event.participants.set(participants_ids)

        return redirect("events_list")

    return render(request, "rawd_pages/edit_event.html", {"event": event, "students": students})


def remove_event(request, id):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    event = get_object_or_404(Event, id=id)
    event.delete()
    messages.success(request, "تمت إزالة النشاط بنجاح")
    return redirect('events_list')


# ======================== FINANCIALS VIEW ========================

def rawd_financials(request):
    if not request.user.is_authenticated:
        return redirect('rawd_login')
    
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
    else:
        start_date = date.today().replace(day=1)
        end_date = date.today()

    # Payments - exclude None dates
    payments = StudentPayment.objects.filter(date__isnull=False, date__range=[start_date, end_date])
    total_payments = payments.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)

    # Expenses - exclude None dates
    expenses = SchoolExpense.objects.filter(date__isnull=False, date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(Sum("amount"))["amount__sum"] or Decimal(0)

    # Events - exclude None dates
    events = Event.objects.filter(date__isnull=False, date__range=[start_date, end_date])
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

    # Calculate rent
    school = School.objects.first()
    rent_per_month = Decimal(school.rent_amount) if school else Decimal(0)
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month + 1)
    rent_total = rent_per_month * months

    # Net profit
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