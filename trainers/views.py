from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render,redirect,get_object_or_404
from django.utils.timezone import datetime
from django.db.models import Sum, F, Count
from .models import *
import json
from django.contrib import messages
from django.utils import timezone
from .models import Trainer, Payments
import calendar
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required



@login_required(login_url='/login/')
def Home(request):
    if request.user.is_superuser:
        now = timezone.now()
        today = now.date()
        # Financial summaries
        financial_summary = {
            'total_yearly_income': Payments.objects.filter(
                paymentdate__year=today.year
            ).aggregate(total=Sum('paymentAmount'))['total'] or 0,
            'monthly_income': Payments.objects.filter(
                paymentdate__year=today.year,
                paymentdate__month=today.month
            ).aggregate(total=Sum('paymentAmount'))['total'] or 0,
            'today_income': Payments.objects.filter(
                paymentdate=today
            ).aggregate(total=Sum('paymentAmount'))['total'] or 0
        }

        payment_categories = {
            'month': {
                'label': 'شهرية', 
                'frequency': 'monthly', 
                'grace_days': 0
            },
            'subscription': {
                'label': 'انخراط', 
                'frequency': 'yearly', 
                'grace_days': 0
            },
            'assurance': {
                'label': 'التأمين', 
                'frequency': 'yearly', 
                'grace_days': 0
            },'jawaz': {
                'label': 'جواز', 
                'frequency': 'yearly', 
                'grace_days': 0
            }
        }

        payment_status = {}

        for category, category_info in payment_categories.items():
            trainers = Trainer.objects.filter(is_active=True)
            unpaid_trainers = []

            for trainer in trainers:
                # Retrieve the last payment for the trainer in this category
                last_payment = Payments.objects.filter(
                    trainer=trainer,
                    paymentCategry=category
                ).order_by('-paymentdate').first()

                if last_payment:

                    payment_due_date = None
                    
                    if category_info['frequency'] == 'monthly':
                        # Get the last day of the month for the last payment
                        if today.month == 12:
                            next_month = 1
                            year = today.year + 1
                        else:
                            next_month = today.month + 1
                            year = today.year
                        last_day_of_payment_month = calendar.monthrange(
                            year,
                            next_month
                        )[1]  # E.g., 28, 29, 30, or 31
                        payment_due_date = last_payment.paymentdate.replace(
                            day=min(last_payment.paymentdate.day,last_day_of_payment_month),
                            month=next_month,
                            year=year
                        )
                        print(payment_due_date)
                    
                    elif category_info['frequency'] == 'yearly':
                        payment_due_date = last_payment.paymentdate.replace(
                            year=last_payment.paymentdate.year + 1
                        ) + timedelta(days=category_info['grace_days'])

                    # Check if payment is overdue
                    if today > payment_due_date:
                        unpaid_trainers.append({
                            'trainer_name': f"{trainer.first_name} {trainer.last_name}",
                            'last_payment_date': last_payment.paymentdate
                        })
                        
                        
                else:
                    # Trainer has never paid in this category
                    unpaid_trainers.append({
                        'trainer_name': f"{trainer.first_name} {trainer.last_name}",
                        'last_payment_date': None
                    })
            
            payment_status[category] = {
                'label': category_info['label'],
                'unpaid_trainers': unpaid_trainers,
                'total_unpaid_trainers': len(unpaid_trainers)
            }
        # Paid today trainees
        paid_today_trainees = Payments.objects.filter(paymentdate=today).select_related('trainer')
        paid_today_trainees = [
            {
                "trainer_name": f"{payment.trainer.first_name} {payment.trainer.last_name}",
                "payment_date": payment.paymentdate,
                "payment_category": payment.get_paymentCategry_display(),
                "payment_amount": payment.paymentAmount
            }
            for payment in paid_today_trainees
        ]

        # Chart data
        chart_labels = [str(m) for m in range(1, 13)]  # Months 1-12
        chart_data = {category: [0] * 12 for category in payment_categories}

        for category in payment_categories:
            category_income = Payments.objects.filter(
                paymentCategry=category,
                paymentdate__year=today.year
            ).values('paymentdate__month').annotate(
                total_income=Sum('paymentAmount')
            )

            for entry in category_income:
                month = entry['paymentdate__month'] - 1
                chart_data[category][month] = entry['total_income']

        # Prepare context
        context = {
            'financial_summary': financial_summary,  # Financial overview
            'chart_labels': json.dumps(chart_labels),  # Chart labels
            'chart_data': {key: json.dumps(value) for key, value in chart_data.items()},  # Chart data
            'payment_status': payment_status,  # Payment tracking details
            'paid_today_trainees': paid_today_trainees,  # Trainees who paid today
            
        }

        return render(request, "pages/index.html", context)
    return redirect('dashboard')


"""
def Home(request):
    # Get today's date
    today = datetime.now().date()
    today_day = today.day  # Day of the month

    # Determine the last day of the current month
    _, last_day_of_month = calendar.monthrange(today.year, today.month)

    # Lists for trainees
    paid_today_trainees = []
    due_today_trainees = []
    total_year_monthes = 0
    total_month =0
    newpayment=0
    newtrainer=0

    for trainee in Trainer.objects.all():
        # Get all payments for this trainee
        trainee_payments = Payments.objects.filter(trainer=trainee,paymentCategry="month").order_by("-paymentdate")
        
        if trainee_payments.exists():
            # Get the most recent payment
            if trainee_payments.first().paymentdate.month == today.month and trainee_payments.first().paymentdate.year==today.year:
                total_month += trainee_payments.first().paymentAmount
            last_payment = trainee_payments.first()
            for pay in trainee_payments:
                total_year_monthes += pay.paymentAmount

            if last_payment.paymentdate == today:
                # Trainee has paid today
                newpayment += last_payment.paymentAmount
                if trainee.started_day == today:newtrainer += 1
                
                paid_today_trainees.append({
                    "trainee_name": trainee.last_name,
                    "last_payment_date": last_payment.paymentdate,
                })
            else:
                payment_due_day = min(last_payment.paymentdate.day, last_day_of_month)
                if (
                    payment_due_day <= today_day and
                    (last_payment.paymentdate.month < today.month or last_payment.paymentdate.year < today.year)
                ):
                    due_today_trainees.append({
                        "trainee_name": trainee.last_name,
                        "last_payment_date": last_payment.paymentdate,
                    })
        else:
            # If no payments exist, trainee is due today
            due_today_trainees.append({
                "trainee_name": trainee.last_name,
                "last_payment_date": None,
            })



    monthly_data = (
        Payments.objects.annotate(month=TruncMonth('paymentdate'))
        .values('month')
        .annotate(total=Sum('paymentAmount'))
        .order_by('month')
    )

    # Prepare the data for the chart
    chart_labels = [entry['month'].strftime('%Y-%m') for entry in monthly_data]
    chart_data = [entry['total'] for entry in monthly_data]

    
            

    return render(request, "pages/index.html", {
        "paid_today_trainees": paid_today_trainees,
        "due_today_trainees": due_today_trainees,
        "totalyear" : total_year_monthes,
        "totalmonth" : total_month,
        "newpayment":newpayment,
        "newtrainer":newtrainer,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })

"""

@login_required(login_url='/login/')
def add_trainee(request):
        first_name=None; last_name=None; birthday=None; gender=None; phone=None; email=None; category=None; cin=None;upload=None
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            birthday = request.POST.get('birthday')
            gender = request.POST.get('gender')
            phone = request.POST.get('phone')
            phone_parent = request.POST.get('phone_parent')
            email = request.POST.get('email')
            address = request.POST.get('address')
            cin = request.POST.get('cin')
            education = request.POST.get('education')
            belt = request.POST.get('belt')
            upload = request.FILES['upload']
            category = request.POST.get('category')
            height = request.POST.get('height')
            weight = request.POST.get('weight')

            if first_name and last_name and birthday and gender and phone and email and category and cin:
                Trainer(first_name=first_name,last_name=last_name,birth_day=birthday,phone=phone,email=email,
                        address=address,CIN=cin, male_female=gender,belt_degree=belt,Degree=education,category=category,
                        started_day=datetime.today(),image=upload,tall=height,weight=weight,phone_parent=phone_parent
                        ).save()
        return render(request,"pages/add_trainee.html")

@login_required(login_url='/login/')
def add_women(request):
        first_name=None; last_name=None; birthday=None; gender=None; phone=None; email=None; category=None; cin=None
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            birthday = request.POST.get('birthday')
            gender = request.POST.get('gender')
            phone = request.POST.get('phone')
            phone_parent = request.POST.get('phone_parent')
            email = request.POST.get('email')
            address = request.POST.get('address')
            cin = request.POST.get('cin')
            education = request.POST.get('education')
            belt = request.POST.get('belt')
            if 'upload' in request.FILES:upload = request.FILES['upload']

            
            category = request.POST.get('category')
            height = request.POST.get('height')
            weight = request.POST.get('weight')

            if first_name and last_name and birthday and gender and phone and email and category and cin:
                Trainer(first_name=first_name,last_name=last_name,birth_day=birthday,phone=phone,email=email,
                        address=address,CIN=cin, male_female=gender,belt_degree=belt,Degree=education,category=category,
                        started_day=datetime.today(),image=upload,tall=height,weight=weight,phone_parent=phone_parent
                        ).save()
        return render(request,"pages/add_women.html")

@login_required(login_url='/login/')
def add_payment(request):
        if request.method == 'POST':
            trainer_id = request.POST.get('trainer')
            paymentdate = request.POST.get('paymentdate')
            paymentCategry = request.POST.get('paymentCategry')
            paymentAmount = request.POST.get('paymentAmount')

            # إنشاء كائن جديد للدفع
            trainer = Trainer.objects.get(id=trainer_id)
            payment = Payments(
                trainer=trainer,
                paymentdate=paymentdate,
                paymentCategry=paymentCategry,
                paymentAmount=paymentAmount
            )
            payment.save()
            
            return redirect('added_payment')  
    
        trainers = Trainer.objects.all()
        return render(request, 'pages/add_payment.html', {'trainers': trainers})

@login_required(login_url='/login/')
def added_payment(request):
    if request.user.is_authenticated:
        return render(request,"pages/added_payment.html")

def payments_history(request):
    if request.user.is_authenticated:
        context = {'payments':Payments.objects.all()}
        return render(request,"pages/payments_history.html",context)

@login_required(login_url='/login/')
def payments_del(request,id):
        Payments.objects.get(pk=id).delete()
        return redirect("payments_history")

@login_required(login_url='/login/')
def payment_edit(request, id):
    if request.user.is_authenticated:
    # استرجاع الدفعة باستخدام معرّفها
        payment = get_object_or_404(Payments, id=id)

        if request.method == "POST":
            # تحديث البيانات الواردة من النموذج
            payment.paymentCategry = request.POST.get("paymentCategry")
            payment.paymentdate = request.POST.get("paymentdate")
            payment.paymentAmount = request.POST.get("paymentAmount")
            
            # حفظ التعديلات
            payment.save()
            #messages.success(request, "تم تحديث بيانات الدفعة بنجاح!")
            return redirect("payments_history")  # تعديل وجهة الإعادة كما هو مطلوب

        # إذا كانت الطلبية GET، عرض النموذج مع البيانات الحالية
        return render(request, "pages/edit_payment.html", {"payment": payment})





from django.db.models import Q
@login_required(login_url='/login/')
def trainees(request,category):
    trainers = Trainer.objects.all()
    if category!="all":
        trainers = Trainer.objects.filter(category=category)
    else:
        trainers = trainers.exclude(category="women")
    if request.method == "GET":
        if 'gender' in request.GET and request.GET['gender']:trainers= trainers.filter(male_female= request.GET['gender'])
        if 'order' in  request.GET:
            if request.GET['order']=='first_first':trainers= trainers.order_by('-started_day')
            if request.GET['order']=='last_first':trainers= trainers.order_by('started_day')
            if request.GET['order']=='first_name':trainers= trainers.order_by('last_name')
                    
    
    template = loader.get_template('pages/olders.html')
    return HttpResponse(template.render({'trainers':trainers,'number':trainers.count()},request))




@login_required(login_url='/login/')
def trainee_profile(request, id):
    # Get all payments for the trainee
    trainee_payments = Payments.objects.filter(trainer_id=id).order_by("paymentdate")  # Adjust as needed
    articles = Article.objects.filter(trainees = Trainer.objects.get(pk=id))

    # Determine the range of months
    if trainee_payments.exists():
        first_payment_date = trainee_payments.first().paymentdate
        start_month = datetime(first_payment_date.year, first_payment_date.month, 1)
    else:
        # Default to current month if no payments exist
        start_month = datetime(datetime.now().year, datetime.now().month, 1)

    # Generate months from the first payment to the current month
    current_month = datetime.now()
    months = []
    while start_month <= current_month:
        months.append(start_month.strftime("%Y-%m"))
        # Move to the next month
        if start_month.month == 12:
            start_month = datetime(start_month.year + 1, 1, 1)
        else:
            start_month = datetime(start_month.year, start_month.month + 1, 1)

    # Track paid months
    paid_months = {payment.paymentdate.strftime("%Y-%m") for payment in trainee_payments}

    # Prepare context with payment status
    payment_status = [
        {"month": month, "status": "paid" if month in paid_months else "unpaid"}
        for month in months
    ]

    return render(request, "pages/profile.html", {"payment_status": payment_status,"trainers":Trainer.objects.get(pk=id),'articles':articles})

@login_required(login_url='/login/')
def delete_trainer_view(request, id):
    # استرجاع المدرب وحذفه
    trainer = get_object_or_404(Trainer, id=id)
    cat = trainer.category
    trainer.delete()
    messages.success(request, "تم حذف المدرب بنجاح.")
    return redirect("trainees",'all')  # استبدل "trainers_list" بمسار القائمة الرئيسية


@login_required(login_url='/login/')
def edit_trainee(request, id):
    trainee = get_object_or_404(Trainer, id=id)
    if request.method == 'POST':
        trainee.first_name = request.POST['first_name']
        trainee.last_name = request.POST['last_name']
        trainee.birth_day = request.POST['birthday']
        trainee.male_female = request.POST['gender']
        trainee.email = request.POST['email']
        trainee.phone = request.POST['phone']
        trainee.phone_parent = request.POST['phone_parent']
        trainee.address = request.POST['address']
        trainee.belt_degree = request.POST['belt']
        trainee.category = request.POST['category']
        trainee.weight = request.POST['weight']
        trainee.tall = request.POST['height']
        trainee.CIN = request.POST['cin']
        trainee.is_active = 'is_active' in request.POST
        if 'upload' in request.FILES:
            trainee.image = request.FILES['upload']
        trainee.save()
        return redirect("profile",trainee.pk)  # توجيه إلى قائمة المتدربين
    return render(request, 'pages/edit_trainee.html', {'trainee': trainee})




def success(request):
    return render(request, 'pages/sucss.html')




#JAWAZ
@login_required(login_url='/login/')
def add_article(request):
    if request.method == "POST":
        title = request.POST['title']
        date = request.POST.get('date', timezone.now())
        content = request.POST['content']
        area = request.POST.get('area')
        category = request.POST.get('category')
        trainees_ids = request.POST.getlist('trainees')
        participetion_price = request.POST['payed']
        costs = request.POST['costs']
        location = request.POST.get('location')

        # إنشاء المقال
        article = Article.objects.create(
            title=title,
            area = area,
            category=category,
            date=date,
            content=content,
            costs = costs,
            location=location,
            participetion_price=participetion_price
        )

        # ربط المدربين بالمقال
        if trainees_ids:
            trainees = Trainer.objects.filter(id__in=trainees_ids)
            article.trainees.set(trainees)

        return redirect('articles/all')  # وجه إلى صفحة المقالات بعد الحفظ

    # بيانات المدربين لإظهارها في القائمة
    trainers = Trainer.objects.all()
    return render(request, 'pages/add_Article.htm', {'trainers': trainers, 'date': timezone.now().date()})


@login_required(login_url='/login/')
def articles(request,category):
    if category != 'all':
        articles = Article.objects.filter(category=category)
    else:
        articles = Article.objects.all()
    context = {
        'articles':articles,
        'number':articles.count()
    }
    return render(request,'pages/articles.html',context)

def article_details(request,id):
    article = Article.objects.get(pk=id)
    
    con = {'article' : article
           }
    return render(request,'pages/article_detail.html',con)

#Financil
from calendar import monthrange
from datetime import datetime, timedelta

@login_required(login_url='/login/')
def finantial_status(request):
    # Retrieve start and end dates from GET parameters
    start = request.GET.get('start', '2024-01-01')
    end = request.GET.get('end', '2024-12-31')
    
    # Convert string dates to datetime objects and then to date objects
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    
    # Initialize totals
    rent_total = 0
    staff_total = 0

    # Calculate recurring rent payments
    organization_info = OrganizationInfo.objects.first() # Assuming one organization info record
    if organization_info:
        rent_day = organization_info.datepay.day
        current_date = organization_info.datepay

        # Count the number of times the rent day occurs in the range
        rent_count = 0
        while current_date <= end_date:
            if current_date >= start_date:
                rent_count += 1
            # Move to the next month
            days_in_month = monthrange(current_date.year, current_date.month)[1]
            current_date += timedelta(days=days_in_month)

        rent_total = rent_count * organization_info.rent_amount

    # Calculate recurring staff payments
    staff = Staff.objects.all()
    for staff_member in staff:
        pay_day = staff_member.datepay.day
        current_date = staff_member.datepay

        # Count the number of times the pay day occurs in the range
        pay_count = 0
        while current_date <= end_date:
            if current_date >= start_date:
                pay_count += 1
            # Move to the next month
            days_in_month = monthrange(current_date.year, current_date.month)[1]
            current_date += timedelta(days=days_in_month)

        staff_total += pay_count * staff_member.salary

    # Calculate other costs and profits
    date__range = [start, end]
    costs = Costs.objects.filter(date__range=date__range)
    articles = Article.objects.filter(date__range=date__range)
    total_added_costs = sum([x.amount for x in costs])
    total_article_costs = sum([x.costs for x in articles])
    total_costs = total_added_costs + total_article_costs + rent_total + staff_total
    arts_pro = sum([x.profit for x in articles])
    added_payments = Addedpay.objects.filter(date__range=date__range)
    total_added_pay = sum([x.amount for x in added_payments])
    payments = Payments.objects.filter(paymentdate__range=date__range)
    payments_total = sum([x.paymentAmount for x in payments.filter(paymentCategry='month' or 'subscription')])
    profit = payments_total + total_added_pay + arts_pro
    
    # Count payers by category
    payers_nbs = {
        'big': payments.filter(trainer_id__category='big').count(),
        'med': payments.filter(trainer_id__category='med').count(),
        'small': payments.filter(trainer_id__category='small').count(),
    }

    # Prepare context
    context = {
        'costs': costs,
        'total_costs': total_costs,
        'profit': profit,
        'net_profit': profit - total_costs,
        'numbers': payers_nbs,
        'articles_nb': articles.count(),
        'artspro': arts_pro,
        'payments_total': payments_total,
        'addedpayments': added_payments,
        'total_added_pay': total_added_pay,
        'added_expenses': costs,
        'total_added_costs': total_added_costs,
        'total_article_costs': total_article_costs,
        'staff': staff,
        'staff_total': staff_total,  # Total salaries
        'rent_total': rent_total,  # Total rent
        'org': organization_info,
        'start': start,
        'end': end,
    }


    return render(request,'pages/finantial_status.html',context)
"""
import openai

def generate_ai_insights(data):
    openai.api_key = "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"
    
    prompt = f"Provide observations and insights based on the following financial data: {data}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        #=[
            {"role": "system", "content": "You are a financial advisor."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

    # Print the assistant's reply
    """
    

@login_required(login_url='/login/')
def add_payments(request):
    if request.method == "POST":
        # Handle form submission directly from POST data
        
            title = request.POST.get("title")
            date = request.POST.get("date")
            description = request.POST.get("description")
            amount = float(request.POST.get("amount"))

            # Create a new expense entry
            Addedpay(
                date=date,
                desc=description,
                amount=amount,
                title = title
            ).save()
            return redirect("finantial_status")  # Redirect back to the same page after saving
    else:
            return render(
                request,
                "pages/add_payments.html",
       )


@login_required(login_url='/login/')
def add_expenses(request):
    if request.method == "POST":
        # Handle form submission directly from POST data
        
            title = request.POST.get("title")
            date = request.POST.get("date")
            category = request.POST.get("category")
            description = request.POST.get("description")
            amount = float(request.POST.get("amount"))

            # Create a new expense entry
            Costs(
                date=date,
                is_allways=category,
                desc=description,
                amount=amount,
                cost = title
            ).save()
            return redirect("finantial_status")  # Redirect back to the same page after saving
    else:
            return render(
                request,
                "pages/add_expenses.html",
       )
    #return render(request, "pages/add_expenses.html")

## MAnagin staff

@login_required(login_url='/login/')
def add_staff(request):
    if request.user.is_superuser:
        if Staff.objects.filter(user=request.user).exists():pass
        else : Staff.objects.create(
                user=request.user,
                role='ADMIN',
                is_admin=True,
                salary=0,
                started = timezone.now()
            )

        if request.method == "POST":
            # الحصول على البيانات من النموذج
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            salary = float(request.POST.get('salary'))
            is_admin = request.POST.get('is_admin') == 'true'
            date = request.POST.get('date')

            # التحقق من وجود البريد الإلكتروني أو اسم المستخدم لتجنب التكرار
            if User.objects.filter(username=username).exists():
                return render(request, 'pages/add_staff.html', {'error': 'اسم المستخدم موجود بالفعل'})
            
            if User.objects.filter(email=email).exists():

                return render(request, 'pages/add_staff.html', {'error': 'البريد الإلكتروني موجود بالفعل'})

            # إنشاء المستخدم في جدول User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
                
            )

            # إضافة السجل إلى قاعدة البيانات
            Staff.objects.create(
                user=user,
                role=role,
                is_admin=is_admin,
                salary=salary,
                started = date
            )

            # إعادة التوجيه إلى صفحة النجاح
            #return redirect('some_success_page')  # تأكد من تعريف هذا المسار

        # في حال كان الطلب GET فقط، أظهر النموذج
        return render(request, 'pages/add_staff.html')

   # جلب معلومات الجمعية

#infos

@login_required(login_url='/login/')
def staff_list(request):
    if not request.user.is_superuser:
        ##.error(request, "ليس لديك الصلاحيات للوصول إلى هذه الصفحة")
        return redirect('home')
    
    if Staff.objects.filter(user=request.user).exists():pass
    else : Staff.objects.create(
                user=request.user,
                role='ADMIN',
                is_admin=True,
                salary=0,
                started = timezone.now()
            )

    # جلب بيانات الجمعية
    organization = OrganizationInfo.objects.first()

    # جلب قائمة الموظفين
    staff_members = Staff.objects.all()

    return render(request, 'pages/staff_list.html', {
        'organization': organization,
        'staff_members': staff_members,
    })


@login_required(login_url='/login/')
def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)

    if request.method == 'POST':
        staff.user.username = request.POST.get('username')
        staff.role = request.POST.get('role')
        staff.is_admin = request.POST.get('is_admin') == 'true'
        staff.started = request.POST.get('started')
        staff.salary = float(request.POST.get('salary'))

        staff.user.save()
        staff.save()

        #.success(request, "تم تحديث بيانات الموظف بنجاح")
        return redirect('staff_list')

    return render(request, 'pages/edit_staff.html', {'staff': staff})


@login_required(login_url='/login/')
def delete_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    if staff.user.is_superuser:
            return redirect('home')
        
    staff.user.delete()  # يحذف المستخدم المرتبط
    staff.delete()  # يحذف سجل الموظف

    #.success(request, "تم حذف الموظف بنجاح")
    return redirect('staff_list')


@login_required(login_url='/login/')
def edit_organization(request):
    if not request.user.is_superuser:
        organization = OrganizationInfo.objects.exists()
        if organization:
            organization = OrganizationInfo.objects.first()
        if request.method == 'POST':
            if organization:
                organization.name = request.POST.get('name')
                organization.description = request.POST.get('description')
                organization.established_date = request.POST.get('established_date')
                organization.rent_amount = float(request.POST.get('rent_amount'))
                organization.phone_number = request.POST.get('phone_number')
                organization.email = request.POST.get('email')
                organization.datepay = request.POST.get('payrentdate')
                organization.save()

            else:OrganizationInfo.objects.create(name = request.POST.get('name')
                ,description = request.POST.get('description')
                ,established_date = request.POST.get('established_date')
                ,rent_amount = float(request.POST.get('rent_amount'))
                ,phone_number = request.POST.get('phone_number')
                ,email = request.POST.get('email')
                ,datepay = request.POST.get('payrentdate')
                ).save()
            

        
            #.success(request, "تم تحديث بيانات الجمعية بنجاح")
            return redirect('staff_list')

        return render(request, 'pages/edit_organization.html', {'organization': organization})



## LOGIN



def login_view(request):
    if request.user.is_authenticated is not True:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            
            if user :
                # Check if the user is associated with a staff member
                try:
                    staff = user.staff  # Assuming the related name is 'staff'
                    login(request, user)
                    messages.success(request, 'تم تسجيل الدخول بنجاح')
                    if user.is_superuser:return redirect('home')
                    else: return redirect('dashboard')  # Redirect to staff dashboard
                except:
                    messages.error(request, 'غير مصرح بالدخول')
                    return render(request, 'pages/login.html')
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
                return render(request, 'pages/login.html')
        
        return render(request, 'pages/login.html')
    else:
        return redirect('dashboard')

@login_required(login_url='/login/')
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'تم تسجيل الخروج بنجاح')
        return redirect('login')

@login_required(login_url='/login/')
def dashboard(request):
    # Basic staff dashboard view
    try:
        """staff_profile = request.user.staff
        context = {
            'staff': staff_profile
        }"""
        now = timezone.now()
        today = now.date()

        payment_categories = {
            'month': {
                'label': 'شهرية', 
                'frequency': 'monthly', 
                'grace_days': 0
            },
            'subscription': {
                'label': 'انخراط', 
                'frequency': 'yearly', 
                'grace_days': 0
            },
            'assurance': {
                'label': 'التأمين', 
                'frequency': 'yearly', 
                'grace_days': 0
            }
        }

        
        payment_status = {}

        for category, category_info in payment_categories.items():
            trainers = Trainer.objects.filter(is_active=True)
            unpaid_trainers = []

            for trainer in trainers:
                # Retrieve the last payment for the trainer in this category
                last_payment = Payments.objects.filter(
                    trainer=trainer,
                    paymentCategry=category
                ).order_by('-paymentdate').first()

                if last_payment:
                    payment_due_date = None
                    
                    if category_info['frequency'] == 'monthly':
                        # Get the last day of the month for the last payment
                        last_day_of_payment_month = calendar.monthrange(
                            last_payment.paymentdate.year, 
                            last_payment.paymentdate.month
                        )[1]  # E.g., 28, 29, 30, or 31
                        payment_due_date = last_payment.paymentdate.replace(
                            day=min(last_payment.paymentdate.day,last_day_of_payment_month),
                            month=today.month,
                            year=today.year
                        )
                        print(payment_due_date)
                    
                    elif category_info['frequency'] == 'yearly':
                        payment_due_date = last_payment.paymentdate.replace(
                            year=last_payment.paymentdate.year + 1
                        ) + timedelta(days=category_info['grace_days'])

                    # Check if payment is overdue
                    if today > payment_due_date:
                        unpaid_trainers.append({
                            'trainer_name': f"{trainer.first_name} {trainer.last_name}",
                            'last_payment_date': last_payment.paymentdate
                        })
                        
                        
                else:
                    # Trainer has never paid in this category
                    unpaid_trainers.append({
                        'trainer_name': f"{trainer.first_name} {trainer.last_name}",
                        'last_payment_date': None
                    })
            
            payment_status[category] = {
                'label': category_info['label'],
                'unpaid_trainers': unpaid_trainers,
                'total_unpaid_trainers': len(unpaid_trainers)
            }
        # Paid today trainees
        paid_today_trainees = Payments.objects.filter(paymentdate=today).select_related('trainer')
        paid_today_trainees = [
            {
                "trainer_name": f"{payment.trainer.first_name} {payment.trainer.last_name}",
                "payment_date": payment.paymentdate,
                "payment_category": payment.get_paymentCategry_display(),
                "payment_amount": payment.paymentAmount
            }
            for payment in paid_today_trainees
        ]

        for category in payment_categories:
            category_income = Payments.objects.filter(
                paymentCategry=category,
                paymentdate__year=today.year
            ).values('paymentdate__month').annotate(
                total_income=Sum('paymentAmount')
            )

            for entry in category_income:
                month = entry['paymentdate__month'] - 1

        # Prepare context
            context = {
                'payment_status': payment_status,  # Payment tracking details
                'paid_today_trainees': paid_today_trainees,  # Trainees who paid today
            }

            return render(request, 'pages/home.html',context)
    except:
        messages.error(request, 'الوصول غير مسموح')
        return redirect('login')
#Email
from django.core.mail import send_mail

def emails(request):
    con={
        'emails':Emailed.objects.all()
    }

    return render(request,'pages/emails.html',con)


from background_task import background

@background
def send_payment_reminder():
    today = timezone.now().date()
    print("=================================================================\n")
    print(today)
    # Payment categories with labels and frequencies
    payment_categories = {
        'month': {'label': 'الشهر', 'frequency': 'monthly'},
        'subscription': {'label': 'الانخراط', 'frequency': 'yearly'},
        'assurance': {'label': 'التأمين', 'frequency': 'yearly_A'},
    }

    for category, category_info in payment_categories.items():
        trainers = Trainer.objects.filter(is_active=True)

        for trainer in trainers:
            # Fetch the most recent payment
            last_payment = Payments.objects.filter(
                trainer=trainer,
                paymentCategry=category
            ).order_by('-paymentdate').first()

            if last_payment:
                start_date = last_payment.paymentdate  # Last payment date

                # Determine the next payment due date
                if category_info['frequency'] == 'monthly':
                    due_day = start_date.day

                    # Handle end-of-month payments
                    if due_day == calendar.monthrange(start_date.year, start_date.month)[1]:
                        due_day = calendar.monthrange(today.year, today.month)[1]

                    due_date = today.replace(day=due_day) if today.day <= due_day else None
                else:  # Yearly payments (subscription, assurance)
                    due_date = start_date.replace(year=today.year)

                # Ensure the due_date is valid and today matches it
                if not due_date or today != due_date:
                    continue
 
                # Check if an email has already been sent for this user, category, and day
                if not Emailed.objects.filter(
                    user=trainer,
                    category=category_info['label'],
                    datetime=today
                ).exists():
                    # Prepare the email body
                    email_subject = f"تذكير بدفع مستحقات {category_info['label']}"
                    email_message = (
                        f"عزيزي {trainer.first_name} {trainer.last_name},\n\n" if trainer.male_female=="male" else f"عزيزتي {trainer.first_name} {trainer.last_name},\n\n" 
                        
                        f"نود تذكيرك بأن موعد دفع مستحقات  '{category_info['label']}' "
                        f"يوافق اليوم ({due_date}).\n"
                        f"الرجاء إتمام الدفع.\n\n"
                        f"إذا كنت بحاجة إلى أي مساعدة، لا تتردد في التواصل مع الادارة.\n\n"
                        f"شكرًا لك،\n"
                        f"إدارة نجوم أركانة"
                    )
 
                    # Send the reminder email
                    send_mail(
                        subject=email_subject,
                        message=email_message,
                        from_email="youness.bouhnif.84@edu.uiz.ac.ma",
                        recipient_list=[trainer.email],
                        fail_silently=False,
                    )

                    # Log the email in the database
                    Emailed.objects.create(
                        user=trainer,
                        email=trainer.email,
                        category=category_info['label'],
                        datetime=timezone.now(),
                    )
                    print(f"Reminder email sent to {trainer.email} for category {category_info['label']}")
                else:
                    print(f"Email already sent to {trainer.email} for category {category_info['label']} today.")
                print("======================================================")

from trainers.tasks import send_payment_reminder_task

# Schedule the task to run daily
send_payment_reminder_task(repeat=60*60*24)

#handling errors



from django.http import JsonResponse

@login_required
def edit_article(request, id):
    article = get_object_or_404(Article, id=id)
    trainees = Trainer.objects.all()

    if request.method == 'POST':
        
            # Update basic article information
            article.title = request.POST.get('title')
            article.date = request.POST.get('date')
            article.location = request.POST.get('location')
            article.participetion_price = float(request.POST.get('profitpayed', 0))
            article.costs = float(request.POST.get('costs', 0))
            article.content = request.POST.get('content')
            
                        
            # Update trainees
            selected_trainees = request.POST.getlist('trainees')
            article.trainees.clear()
            article.trainees.add(*selected_trainees)
            
            # Save the article
            article.save()
            
            messages.success(request, 'تم تحديث المقالة بنجاح')
            return redirect('article_detail', id=article.id)
            
       
    
    context = {
        'article': article,
        'trainees_art': article.trainees.all(),
        'trainees': trainees,
    }
    
    return render(request, 'pages/edit_article.html', context)

