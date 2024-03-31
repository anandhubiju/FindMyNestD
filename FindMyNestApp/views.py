from django.shortcuts import get_object_or_404, render, redirect
from UserApp.models import CustomUser, ExecutiveProfile, UserProfile ,AgentProfile,AgentView
from Customer.models import HomeInteriors, LoanApplicant, Property
from .models import Subscription,Payment
from django.urls import reverse
from django.views import View
from django.contrib.auth import get_user_model
from .forms import SubscriptionForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
import razorpay
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.core.mail import send_mail, EmailMessage
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
import random
import string
from django.contrib.auth.models import Group


User = get_user_model()

def index(request):
    # Check if the user is authenticated and logged in with Google
    if request.user.is_authenticated:
        if request.user.user_type == CustomUser.ADMIN:
            return redirect(reverse('admindashboard'))
        elif request.user.user_type == CustomUser.AGENT:
            return redirect(reverse('agentdashboard'))
        elif request.user.user_type == CustomUser.EXECUTIVE:
            return redirect(reverse('executivedashboard'))
        elif request.user.user_type == CustomUser.EDITOR:
            return redirect(reverse('editordashboard'))
        elif not request.user.phone_no:
            return render(request, 'profile_completion.html', {'user': request.user})

    # Get the 5 most recently added properties based on the 'created_at' field
    recent_properties = Property.objects.order_by('-created_at')[:5]

    # Retrieve subscription features from a specific Subscription instance
    # # You may want to retrieve a specific subscription
    subscription = Subscription.objects.values().first()
    payment = Payment.objects.filter(payment_status=Payment.PaymentStatusChoices.SUCCESSFUL)
# Load the first subscription

    if subscription:
        features_str = subscription['features']  # Get the 'features' field as a string
        features = features_str.split(',') if features_str else []
    else:
        features = []

    # Get unique property types
    property_types = Property.objects.values_list('property_type', flat=True).distinct()

    # For Razorpay integration
    

    # Retrieve subscription data
    subscriptions = Subscription.objects.all()

    # Prepare the context data
    context = {
        'user': request.user,
        'recent_properties': recent_properties,
        'property_types': property_types,
        'razorpay_merchant_key': settings.RAZOR_KEY_ID,
        'subscriptions': subscriptions,
        'features': features,# Add features to the context
        'payment':payment
    }

    return render(request, 'index.html', context=context)

def payment(request, sub_id):
    # Use get_object_or_404 to get the Subscription object based on sub_id
        # Retrieve subscription features from a specific Subscription instance
    # You may want to retrieve a specific subscription
    subscriptions = Subscription.objects.all()
    
    sub_type = Subscription.objects.get(pk=sub_id)

    if sub_type:
        features_str = sub_type.features  # Get the 'features' field as a string
        features = features_str.split(',') if features_str else []
    else:
        features = []

    # Get unique property types
    property_types = Property.objects.values_list('property_type', flat=True).distinct()

    # For Razorpay integration
    currency = 'INR'
    amount = sub_type.price  # Get the subscription price
    amount_in_paise = int(amount * 100)  # Convert to paise

    # Create a Razorpay Order
    razorpay_order = razorpay_client.order.create(dict(
        amount=amount_in_paise,
        currency=currency,
        payment_capture='0'
    ))

    # Order ID of the newly created order
    razorpay_order_id = razorpay_order['id']
    callback_url = '/paymenthandler/'  # Define your callback URL here


    payment = Payment.objects.create(
        user=request.user,
        razorpay_order_id=razorpay_order_id,
        payment_id="",
        amount=amount,
        currency=currency,
        payment_status=Payment.PaymentStatusChoices.PENDING,
    )
    payment.sub_type.add(sub_type)

    # Prepare the context data
    context = {
        'user': request.user,
        'property_types': property_types,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': settings.RAZOR_KEY_ID,
        'razorpay_amount': amount_in_paise,
        'currency': currency,
        'amount': amount_in_paise / 100,
        'callback_url': callback_url,
        'subscriptions': subscriptions,
        'features': features,  # Add features to the context
        'sub_type': sub_type,
    }

    return render(request, 'Payment.html', context)



def about(request):
    property_types = Property.objects.values_list('property_type', flat=True).distinct()
    return render(request,'about.html',{'property_types': property_types})

def dashboard(request):
    property_types = Property.objects.values_list('property_type', flat=True).distinct()
    return render(request,'dashboard.html',{'property_types': property_types})

def add_subscription(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            sub_type = form.cleaned_data['sub_type']
            price = form.cleaned_data['price']
            validity = form.cleaned_data['validity']
            features_list = form.cleaned_data['features'].split(',')
            features_csv = ','.join(features_list)
            

            if Subscription.objects.filter(
                sub_type=sub_type,
                price=price,
                validity=validity,
                features=features_csv
            ).exists():
                
                form.add_error(None, "A subscription with the same data already exists.")
            else:
               
                subscription = form.save(commit=False)
                subscription.features = features_csv
                subscription.save()
                return redirect('admindashboard')
    else:
        form = SubscriptionForm()
    
    return render(request, 'add_subscription.html', {'form': form})

def generate_username(first_name, last_name):
    base_username = (first_name + last_name).lower()
    potential_username = base_username + ''.join(random.choices(string.ascii_letters, k=5)).lower()

    while User.objects.filter(username=potential_username).exists():
        potential_username = base_username + ''.join(random.choices(string.ascii_letters, k=5)).lower()

    return potential_username

def generate_password(name):
    # Use a simple password generation logic (you may want to implement a more secure approach)
    password = name.lower() + '123'
    return password


def add_agent(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', None)
        last_name = request.POST.get('last_name', None)
        email = request.POST.get('email', None)
        phone = request.POST.get('phone', None)
        password = generate_password(first_name)
        username = generate_username(first_name, last_name)

        if username and first_name and last_name and email and phone and password:

            if User.objects.filter(username=username).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=username_is_already_registered')

            elif User.objects.filter(email=email).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=email_is_already_registered')

            elif User.objects.filter(phone_no=phone).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=phone_no_is_already_registered')

            else:
                user = User(username=username, first_name=first_name, last_name=last_name, email=email, phone_no=phone)
                user.set_password(password)
                user.user_type = CustomUser.AGENT
                user.save()

                user_profile = UserProfile(user=user)
                user_profile.save()
                agent_profile = AgentProfile(user=user)
                agent_profile.save()

                # Send welcome email
                send_email(user.username,user.first_name,user.last_name,user.email,password)

                response = HttpResponseRedirect(reverse('add_agent') + '?alert=registered')
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response

    return render(request, 'add_agent.html')

def send_email(username, first_name, last_name, email, password):
    subject = 'Welcome to FindMyNest'
    message = f"Hello {first_name},\n\n"
    message += f"Welcome to FindMyNest, your platform for real estate agents. We are excited to have you join us!\n\n"
    
    # Retrieve the associated subscription object
    message += f"You have successfully registered as a real estate agent with username {username}.\n\n"
    message += f"Your temporary password is: {password}\n\n"
    
    message += "Please login to your account using this temporary password and update your password as soon as possible.\n\n"
    message += "Thank you for choosing FindMyNest. We look forward to your success as a real estate agent!\n\n"
    message += "Warm regards,\nThe FindMyNest Team\n\n"
    
    from_email = 'findmynest.info@gmail.com'  # Replace with your actual email
    recipient_list = [email]

    # Send the email
    send_mail(subject, message, from_email, recipient_list)


 # Replace 'search.html' with your template

razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

@csrf_exempt
def paymenthandler(request):
    # only accept POST request.
    if request.method == "POST":
        try:
            # get the required parameters from post request.
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # verify the payment signature.
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            if result is not None:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                amount = int(payment.amount * 100)  # Convert Decimal to paise
                try:
                    # capture the payment
                    razorpay_client.payment.capture(payment_id, amount)
                    payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

                    # Update the order with payment ID and change status to "Successful"
                    payment.payment_id = payment_id
                    payment.payment_status = Payment.PaymentStatusChoices.SUCCESSFUL
                    payment.save()

                    # Send the welcome email with PDF invoice
                    send_welcome_email(payment.user.username, payment.sub_type, payment.amount, payment.user.email, payment,)
                    
                    # render success page on successful capture of payment
                    return render(request, 'index.html')
                except:
                    # if there is an error while capturing payment.
                    payment.payment_status = Payment.PaymentStatusChoices.FAILED
                    return render(request, 'paymentfail.html')
            else:
                # if signature verification fails.
                payment.payment_status = Payment.PaymentStatusChoices.FAILED
                return render(request, 'paymentfail.html')
        except:
            # if we don't find the required parameters in POST data
            return HttpResponseBadRequest()
    else:
        # if other than POST request is made.
        return HttpResponseBadRequest()

    
def send_welcome_email(username, sub_type, amount, email, payment):
    subject = 'Welcome to FindMyNest'
    message = f"Hello {username},\n\n"
    message += f"Welcome to FindMyNest, your platform for finding your dream property. We are excited to have you join us!\n\n"
    
    # Retrieve the associated subscription object
    subscription = sub_type.first()  # Assuming sub_type is a ManyToMany field

    if subscription:
        message += f"You have subscribed to the {subscription.sub_type} plan, which is valid for {subscription.validity}.\n\n"
    
    message += "Please feel free to contact the property owner for more information or to schedule a viewing of the property.\n\n"
    message += "Thank you for choosing FindMyNest. We wish you the best in your property search!\n\n"
    message += "Warm regards,\nThe FindMyNest Team\n\n"
    
    from_email = 'findmynest.info@gmail.com'  # Replace with your actual email
    recipient_list = [email]

    # Create a PDF invoice and attach it to the email
    pdf_invoice = generate_pdf_invoice(username, sub_type, amount, payment)
    email = EmailMessage(subject, message, from_email, recipient_list)
    email.attach(f"{username}_invoice.pdf", pdf_invoice, 'application/pdf')

    # Send the email
    email.send()

def generate_pdf_invoice(username, sub_type, amount, payment):
    # Create a PDF document using xhtml2pdf
    template_path = "invoice1.html"  # Replace with the path to your HTML template
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{username}_invoice.pdf"'

    template = get_template(template_path)
    context = {
        'username': username,
        'sub_type': sub_type,
        'amount': amount,
        'payment': payment # Format the timestamp as desired
        }
    html = template.render(context)

    pdf_buffer = io.BytesIO()
    pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), pdf_buffer)

    pdf_content = pdf_buffer.getvalue()
    pdf_buffer.close()

    return pdf_content




@login_required
def search_property(request):
    query = request.GET.get('query')
    print("Query:", query)

   
    if query:
        properties = Property.objects.filter(
            Q(property_type__icontains=query) | Q(Town__icontains=query) | Q(state__icontains=query) | Q(bedrooms__icontains=query) | Q(price__icontains=query) | Q(area__icontains=query)
        )
    else:
       
        properties = []
    property_data = []
    
    for property in properties:
        
        property_dict = {
            'id': property.pk,
            'thumbnail': property.thumbnail.url,
            'address':  property.address,
            'property_type':  property.property_type,
            'bathrooms':  property.bathrooms,
            'bedrooms':  property.bedrooms,
            'price':  property.price,
            'area':  property.area,
        }
        property_data.append(property_dict)

    return JsonResponse({'property': property_data})


def agentlist(request):
    agents=AgentProfile.objects.all()
    property_types = Property.objects.values_list('property_type', flat=True).distinct()

    # Prepare data for rendering
    agent_data = []
    for agent in agents:
        agent_info = {
            'id': agent.pk,
            'full_name': f"{agent.user.first_name} {agent.user.last_name}",
            'email': agent.user.email,
            'phone': agent.user.phone_no,
            'bio': agent.bio,
            'total_cases_dealt': agent.Dcase_no,
            'experience': agent.experience,
            'photo_url': agent.user.userprofile.profile_pic.url if agent.user.userprofile.profile_pic else None,
        }
        agent_data.append(agent_info)
    context = {
        'property_types': property_types,
        'agents': agent_data
        }
    return render(request,'agents-grid.html',context)



def agentsingle(request, agentProfile_id):
    # Retrieve agent from URL parameters
    agent = get_object_or_404(AgentProfile, id=agentProfile_id)

    # Increment the view count
    agent.view_count += 1
    agent.save()

    # Record the user's view
    if request.user.is_authenticated and request.user != agent.user:
        AgentView.objects.get_or_create(agentProfile=agent, user=request.user)

    # Prepare data for rendering
    full_name = f"{agent.user.first_name} {agent.user.last_name}" if agent.user else "N/A"
    photo_url = agent.user.userprofile.profile_pic.url if agent.user and agent.user.userprofile.profile_pic else None

    context = {
        'agent': agent,
        'full_name': full_name,
        'photo': photo_url,
    }

    return render(request, 'agent-single.html', context)

def add_executive(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', None)
        last_name = request.POST.get('last_name', None)
        email = request.POST.get('email', None)
        phone = request.POST.get('phone', None)
        password = generate_password(first_name)
        username = generate_username(first_name, last_name)

        if username and first_name and last_name and email and phone and password:

            if User.objects.filter(username=username).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=username_is_already_registered')

            elif User.objects.filter(email=email).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=email_is_already_registered')

            elif User.objects.filter(phone_no=phone).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=phone_no_is_already_registered')

            else:
                user = User(username=username, first_name=first_name, last_name=last_name, email=email, phone_no=phone)
                user.set_password(password)
                user.user_type = CustomUser.EXECUTIVE
                user.save()

                user_profile = UserProfile(user=user)
                user_profile.save()
                
                executive_profile = ExecutiveProfile(user=user)
                executive_profile.save()


                # Send welcome email
                send_emailE(user.username,user.first_name,user.last_name,user.email,password)

                response = HttpResponseRedirect(reverse('add_agent') + '?alert=registered')
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response

    return render(request, 'add_executive.html')

def add_editor(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', None)
        last_name = request.POST.get('last_name', None)
        email = request.POST.get('email', None)
        phone = request.POST.get('phone', None)
        password = generate_password(first_name)
        username = generate_username(first_name, last_name)

        if username and first_name and last_name and email and phone and password:

            if User.objects.filter(username=username).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=username_is_already_registered')

            elif User.objects.filter(email=email).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=email_is_already_registered')

            elif User.objects.filter(phone_no=phone).exists():
                return HttpResponseRedirect(reverse('add_agent') + '?alert=phone_no_is_already_registered')

            else:
                user = User(username=username, first_name=first_name, last_name=last_name, email=email, phone_no=phone)
                user.set_password(password)
                user.user_type = CustomUser.EDITOR
                user.save()

                user_profile = UserProfile(user=user)
                user_profile.save()
                


                # Send welcome email
                send_emailE(user.username,user.first_name,user.last_name,user.email,password)

                response = HttpResponseRedirect(reverse('add_agent') + '?alert=registered')
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response

    return render(request, 'add_editor.html')

def send_emailE(username, first_name, last_name, email, password):
    subject = 'Welcome to FindMyNest'
    message = f"Hello {first_name},\n\n"
    message += f"Welcome to FindMyNest, your platform for real estate agents. We are excited to have you join us!\n\n"
    
    # Retrieve the associated subscription object
    message += f"You have successfully registered as a real estate agent with username {username}.\n\n"
    message += f"Your temporary password is: {password}\n\n"
    
    message += "Please login to your account using this temporary password and update your password as soon as possible.\n\n"
    message += "Thank you for choosing FindMyNest. We look forward to your success as a real estate agent!\n\n"
    message += "Warm regards,\nThe FindMyNest Team\n\n"
    
    from_email = 'findmynest.info@gmail.com'  # Replace with your actual email
    recipient_list = [email]

    # Send the email
    send_mail(subject, message, from_email, recipient_list)
    
    
@login_required
def home_interiors_details(request):
    # Retrieve all HomeInteriors and LoanApplicant objects
    home_interiors = HomeInteriors.objects.all()

    context = {
        'home_interiors': home_interiors,
    }

    return render(request, 'Home_interiors_details.html', context)

@login_required
def home_Loan_details(request):
    # Retrieve all LoanApplicant objects
    loan_applicants = LoanApplicant.objects.all()

    context = {
        'loan_applicants': loan_applicants,
    }

    return render(request, 'Home_loan_details.html', context)

def update_status(request, user_id):
    home_interiors = HomeInteriors.objects.all()
    if request.method == 'POST':
        # Update the status based on the selected option
        status = request.POST.get('status')
        user = get_object_or_404(HomeInteriors, pk=user_id)        
        user.status = status
        user.save()
        home_interiors = HomeInteriors.objects.all()
        return redirect('home_interiors_details')
    context = {
        'home_interiors': home_interiors,
    }
    return render(request, 'Home_interiors_details.html', context)


def update_statusl(request, user_id):
    if request.method == 'POST':
        status = request.POST.get('status')
        loan_applicant = get_object_or_404(LoanApplicant, pk=user_id)
        loan_applicant.status = status
        loan_applicant.save()
        return redirect('home_Loan_details')
    else:
        return redirect('home_Loan_details')  # Redirect in case of GET request