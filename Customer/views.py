from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from requests import Request
from django.http import JsonResponse
from .models import CompareProperty, Property,Image,PropertyView,Feedback,Wishlist
from .forms import PropertyForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Property, Image 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.http import HttpResponse
from django.http import HttpResponseRedirect
import joblib
import pandas as pd


# Load the trained machine learning model
# Load the trained machine learning model
model = joblib.load('models/seminar.pkl')

# Load label encoders
label_encoders = {}
categorical_columns = ["property_type", "furnished", "air_conditioner", "parking", "water_available"]
for col in categorical_columns:
    le = joblib.load(f'models/{col}_label_encoder.pkl')
    label_encoders[col] = le


# Define a function to extract numerical values and calculate the average
def input_and_average(input_str):
    parts = input_str.split('-')
    values = [float(part) for part in parts if part.replace('.', '', 1).isdigit()]
    return (sum(values) / len(values)) if values else 0.0


# Your login_required decorator

def addproperty(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_instance = form.save(commit=False)
            property_instance.user = request.user
            property_instance.user_type = request.user.user_type

            selected_features = form.cleaned_data['features']
            features_str = ', '.join(selected_features)
            property_instance.features = features_str

            selected_nearby_place = form.cleaned_data['nearby_place']
            nearby_place_str = ', '.join(selected_nearby_place)
            property_instance.nearby_place = nearby_place_str

            distance_to_major_road = input_and_average(form.cleaned_data['major_road'])
            distance_to_supermarket = input_and_average(form.cleaned_data['near_supermarket'])
            property_age = input_and_average(form.cleaned_data['bulding_age'])
            
            last_renovation_years_ago_input = form.cleaned_data['last_renovated']
            last_renovation_years_ago_parts = last_renovation_years_ago_input.split('-')
            last_renovation_years_ago = (int(last_renovation_years_ago_parts[0]) + int(last_renovation_years_ago_parts[1])) // 2

            property_type = form.cleaned_data['property_type']

            if property_type == 'Apartment':
                floor_value = form.cleaned_data['floor_no']
            else:
                floor_value = form.cleaned_data['floor']

            if property_type in ['Commercial', 'Garage']:
                num_bedrooms = 0
            else:
                num_bedrooms = form.cleaned_data['bedrooms']

            furnished = 1 if 'Furnished' in selected_features else 0
            air_conditioner = 1 if 'Air Condition' in selected_features else 0
            parking = 1 if 'Parking' in selected_features else 0
            water_available = 1 if 'Well(Water Availability)' in selected_features else 0

            user_input_dict = {
                'property_type': property_type,
                'num_bedrooms': num_bedrooms,
                'num_bathrooms': form.cleaned_data['bathrooms'],
                'furnished': furnished,
                'air_conditioner': air_conditioner,
                'parking': parking,
                'last_renovation_years_ago': last_renovation_years_ago,
                'water_available': water_available,
                'distance_to_major_road': [distance_to_major_road],
                'distance_to_supermarket': [distance_to_supermarket],
                'price': form.cleaned_data['price'],
                'property_age': [property_age],
                'total_rooms': form.cleaned_data['rooms'],
                'floor': floor_value
            }

            user_input_df = pd.DataFrame(user_input_dict)

            for col, le in label_encoders.items():
                user_input_df[col] = le.transform(user_input_df[col])

            sale_duration_prediction = model.predict(user_input_df)

            property_instance.save()
            property_id = property_instance.id

            images = request.FILES.getlist('images')
            for image in images:
                Image.objects.create(property=property_instance, images=image)

            # Initialize property_tips
            property_tips = []

            # Save the exact number of days to sell
            exact_days_to_sell = int(sale_duration_prediction[0])
            property_instance.days_to_sell = exact_days_to_sell

            # Based on your business logic, you can generate property_tips
            property_tips = []
            
            if exact_days_to_sell > 30:
                property_tips = analyze_property_details(user_input_df.iloc[0])

            # Save property_tips
            property_instance.property_tips = ", ".join(property_tips)  # Join with commas

            sale_duration_tips = []

            # Generate sale_duration_tips
            if exact_days_to_sell <= 30:
                sale_duration_tips.append("Your property is likely to sell quickly. Ensure it's well-maintained for a smooth sale.")
            elif exact_days_to_sell <= 60:
                sale_duration_tips.append("Your property may take a couple of months to sell. Consider staging and effective marketing.")
            else:
                sale_duration_tips.append("Your property may take some time to sell. Focus on competitive pricing and marketing strategies")

            # Set the sale_duration_tips field
            property_instance.sale_duration_tips = ", ".join(sale_duration_tips)  # Join with commas

            property_instance.save()

            # Redirect to the property details page with tips as URL parameters
            return redirect(reverse('property_single', args=[property_id]))
    else:
        form = PropertyForm()

    context = {
        'form': form,
    }
    return render(request, 'addproperty.html', context)


def analyze_property_details(property_details):
    tips = []

    # Example: Analyze property details like 'furnished,' 'air_conditioner,' 'parking,' etc.
    if property_details['furnished'] == 0:
        tips.append("Consider furnishing the property to attract more buyers/renters.")
    if property_details['air_conditioner'] == 0:
        tips.append("Adding air conditioning can make the property more appealing.")
    if property_details['parking'] == 0:
        tips.append("Providing parking can be a significant selling point.")
    if property_details['water_available'] == 0:
        tips.append("Ensure water availability for the property, as it is essential.")
    # Add tips related to renovation based on the last renovation years
    if property_details['last_renovation_years_ago'] >= 5:
        tips.append("Consider renovating the property if it hasn't been renovated in the last 5 years.")

    return tips



import nltk
nltk.download('vader_lexicon') 
from nltk.sentiment import SentimentIntensityAnalyzer
def submit_comment(request):
    if request.method == 'POST':
        # Check if the user is logged in and has a user profile
        if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
            userprofile = request.user.userprofile
        else:
            userprofile = None

        first_name = request.POST['first_name']
        email = request.POST['email']
        message = request.POST['message']
        property_id = request.POST['property_id']
        sentiment_analyzer = SentimentIntensityAnalyzer()        
        sentiment_score = sentiment_analyzer.polarity_scores(message)['compound']  

        # Create a new Feedback instance and save it to the database
        feedback = Feedback(
            userprofile=userprofile,  # Associate feedback with the user's profile
            property_id=property_id,
            first_name=first_name,
            email=email,
            message=message,
            sentiment_score=sentiment_score,
        )
        feedback.save()

        # Optionally, you can add a success message
        # messages.success(request, 'Your comment has been posted successfully.')

        # Redirect to the property_single page with the property_id
        return redirect('property_single', property_id=property_id)

    return render(request, 'property-single.html')



    
def add_wishlist(request, property_id):
    # Get the Property object based on the property_id
    property = get_object_or_404(Property, id=property_id)

    # Create a Wishlist object for the current user and the property
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user, property=property)
        if created:
            message = f'The property "{property.address}" has been added to your wishlist.'
        else:
            message = f'The property "{property.address}" is already in your wishlist.'
    else:
        # Handle the case where the user is not authenticated
        message = 'You need to be logged in to add properties to your wishlist.'

    # You can pass the message to your template or use it as needed
    # For now, we'll just redirect back to the propertylist view
    return redirect('propertylist')

def delete_wishlist(request, property_id):
    wishlist_item = get_object_or_404(Wishlist, property_id=property_id, user=request.user)
    wishlist_item.delete()
    return redirect('propertylist')

def wishlist_view(request):
    if request.user.is_authenticated:
        # Retrieve the wishlist items for the logged-in user
        wishlist_items = Wishlist.objects.filter(user=request.user)
        # Extract the properties from the wishlist items
        wishlist_properties = [item.property for item in wishlist_items]
        return render(request, 'wishlist.html', {'wishlist_properties': wishlist_properties})
    else:
        # Handle the case when the user is not logged in
        # You can redirect them to the login page or display a message
        return render(request, 'wishlist.html', {'wishlist_properties': None})

def propertylist(request):
    properties = Property.objects.all() 
    property_types = Property.objects.values_list('property_type', flat=True).distinct()
    wishlist_items = Wishlist.objects.filter(user=request.user)
    wishlist_property_ids = wishlist_items.values_list('property_id', flat=True)  # Get a list of property IDs = wishlist_items.values_list('property_id', flat=True)  # Get a list of property IDs
    
    print(wishlist_items)
    
    return render(request,'propertylist.html', {'properties': properties,'property_types':property_types,'wishlist_items':wishlist_items,'wishlist_property_ids':wishlist_property_ids})


def property_list_by_type(request, property_type):
   
    properties = Property.objects.filter(property_type=property_type)
    
    context = {
        'properties': properties,
        'selected_property_type': property_type,
        'property_types': property_type
    }
    
    return render(request, 'propertylist_by_type.html', context)


def delete_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)

    if request.user == property.user:
        property.active = False
        property.save()
    
    return redirect('propertylist')

def add_remove_from_wishlist(request):
    property_id = request.POST.get('property_id')
    user = request.user

    try:
        wishlist_item = Wishlist.objects.get(user=user, property_id=property_id)
        wishlist_item.delete()
        added = False
    except Wishlist.DoesNotExist:
        Wishlist.objects.create(user=user, property_id=property_id)
        added = True

    return JsonResponse({'added': added})

def edit_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            updated_property = form.save(commit=False)

            selected_features = form.cleaned_data['features']
            features_str = ', '.join(selected_features)
            updated_property.features = features_str

            selected_nearby_place = form.cleaned_data['nearby_place']
            nearby_place_str = ', '.join(selected_nearby_place)
            updated_property.nearby_place = nearby_place_str

            distance_to_major_road = input_and_average(form.cleaned_data['major_road'])
            distance_to_supermarket = input_and_average(form.cleaned_data['near_supermarket'])
            property_age = input_and_average(form.cleaned_data['bulding_age'])

            last_renovation_years_ago_input = form.cleaned_data['last_renovated']
            last_renovation_years_ago_parts = last_renovation_years_ago_input.split('-')
            last_renovation_years_ago = (int(last_renovation_years_ago_parts[0]) + int(last_renovation_years_ago_parts[1])) // 2

            property_type = form.cleaned_data['property_type']

            if property_type == 'Apartment':
                floor_value = form.cleaned_data['floor_no']
            else:
                floor_value = form.cleaned_data['floor']

            if property_type in ['Commercial', 'Garage']:
                num_bedrooms = 0
            else:
                num_bedrooms = form.cleaned_data['bedrooms']

            furnished = 1 if 'Furnished' in selected_features else 0
            air_conditioner = 1 if 'Air Condition' in selected_features else 0
            parking = 1 if 'Parking' in selected_features else 0
            water_available = 1 if 'Well(Water Availability)' in selected_features else 0

            user_input_dict = {
                'property_type': property_type,
                'num_bedrooms': num_bedrooms,
                'num_bathrooms': form.cleaned_data['bathrooms'],
                'furnished': furnished,
                'air_conditioner': air_conditioner,
                'parking': parking,
                'last_renovation_years_ago': last_renovation_years_ago,
                'water_available': water_available,
                'distance_to_major_road': [distance_to_major_road],
                'distance_to_supermarket': [distance_to_supermarket],
                'price': form.cleaned_data['price'],
                'property_age': [property_age],
                'total_rooms': form.cleaned_data['rooms'],
                'floor': floor_value
            }

            user_input_df = pd.DataFrame(user_input_dict)

            # Process label encoders here
            for col, le in label_encoders.items():
                user_input_df[col] = le.transform(user_input_df[col])

            # Model prediction
            sale_duration_prediction = model.predict(user_input_df)

            # Save the exact number of days to sell
            exact_days_to_sell = int(sale_duration_prediction[0])
            updated_property.days_to_sell = exact_days_to_sell

            # Generate property tips based on business logic
            property_tips = []

            if exact_days_to_sell > 30:
                property_tips = analyze_property_details(user_input_df.iloc[0])

            # Save property_tips
            updated_property.property_tips = ", ".join(property_tips)

            sale_duration_tips = []

            # Generate sale_duration_tips
            if exact_days_to_sell <= 30:
                sale_duration_tips.append("Your property is likely to sell quickly. Ensure it's well-maintained for a smooth sale.")
            elif exact_days_to_sell <= 60:
                sale_duration_tips.append("Your property may take a couple of months to sell. Consider staging and effective marketing.")
            else:
                sale_duration_tips.append("Your property may take some time to sell. Focus on competitive pricing and marketing strategies")

            # Set the sale_duration_tips field
            updated_property.sale_duration_tips = ", ".join(sale_duration_tips)

            updated_property.save()

            images = request.FILES.getlist('images')
            if images:
                # Delete existing property images and add new ones
                Image.objects.filter(property=updated_property).delete()
                for image in images:
                    property_image = Image(property=updated_property, images=image)
                    property_image.save()

            return redirect(reverse('property_single', args=[property_id]))
    else:
        form = PropertyForm(instance=property)

    return render(request, 'edit_property.html', {'form': form, 'property': property })

# def edit_property(request, property_id):
#     property = get_object_or_404(Property, id=property_id)
#     if request.method == 'POST':
        
#         form = PropertyForm(request.POST, request.FILES, instance=property)
    
#         if form.is_valid():
#             updated_property = form.save(commit=False)
            
            
#             selected_features = form.cleaned_data['features']
#             features_str = ', '.join(selected_features)
#             updated_property.features = features_str
            
#             selected_nearby_place = form.cleaned_data['nearby_place']
#             nearby_place_str = ', '.join(selected_nearby_place)
#             updated_property.nearby_place = nearby_place_str

#             images = request.FILES.getlist('images')
#             if images:
                
#                 Image.objects.filter(property=updated_property).delete()
                
#                 for image in images:
#                     property_image = Image(property=updated_property, images=image)
#                     property_image.save()

#             updated_property.save()

#             return redirect('propertylist') 
#     else:
#         form = PropertyForm(instance=property)

#     return render(request, 'edit_property.html', {'form': form, 'property': property })




@login_required
def propertysingle(request, property_id):
    user = request.user
    property = get_object_or_404(Property, id=property_id)
    feedbacks = Feedback.objects.filter(property=property).order_by('-comment_date')

    if request.user != property.user:
        # Increment the view count
        property.view_count += 1
        property.save()

        # Record the user's view
        PropertyView.objects.get_or_create(property=property, user=request.user)

    images = Image.objects.filter(property=property)
    excluded_property_types = ['Commercial', 'Office', 'Garage']
    features = property.features.split(', ') if property.features else []
    nearby_place = property.nearby_place.split(', ') if property.nearby_place else []
    property_tips = property.property_tips.split(', ') if property.property_tips else []
    sale_duration_tips = property.sale_duration_tips.split(', ') if property.sale_duration_tips else []

    # Retrieve properties added to compare by the current user
    compare_properties = CompareProperty.objects.filter(user=user).first()
    compare_property_list = compare_properties.properties.all() if compare_properties else []

    context = {
        'property': property,
        'images': images,
        'user': user,
        'features': features,
        'nearby_place': nearby_place,
        'excluded_property_types': excluded_property_types,
        'feedbacks': feedbacks,
        'sale_duration_tips': sale_duration_tips,
        'property_tips': property_tips,
        'compare_properties': compare_property_list,  # Pass the compare properties to the context
    }

    # Check if the user has added 4 properties to compare
    if len(compare_property_list) >= 4 and property not in compare_property_list:
        messages.error(request, "You cannot add more properties to compare. Remove a property from compare to add another.")
        context['disable_compare_button'] = True

    return render(request, 'property-single.html', context)
    


def viewcontact(request, property_id):
    user = request.user
    property = get_object_or_404(Property, id=property_id)
    
    # Assuming you have a function send_welcome_email that sends the welcome email
    send_welcome_email(property.whatsapp_no, user.email, property.owner_name)
    
    # Return an empty HttpResponse with a success message
    
    return HttpResponseRedirect(reverse('property_single', args=[property_id]) + '?alert=Details_Emailed')

def send_welcome_email(whatsapp_no, email, owner_name):
    subject = 'Welcome to FindMyNest'
    message = f"Hello {email},\n\n"
    message += f"Welcome to FindMyNest, your platform for finding your dream property. We are excited to have you join us!\n\n"
    message += f"Here are the contact details of the property owner:\n\n"
    message += f"Owner Name: {owner_name}\n"
    message += f"WhatsApp No: {whatsapp_no}\n\n"
    message += "Please feel free to contact the property owner for more information or to schedule a viewing of the property.\n\n"
    message += "Thank you for choosing FindMyNest. We wish you the best in your property search!\n\n"
    message += "Warm regards,\nThe FindMyNest Team\n\n"
    
    from_email = 'findmynest.info@gmail.com'  # Replace with your actual email
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list)
    
    
    
    
def like_feedback(request, feedback_id):
    # Check if the request is a POST request
    if request.method == 'POST':
        feedback = get_object_or_404(Feedback, id=feedback_id)

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Check if the user has already liked the feedback
            if feedback.likes.filter(id=request.user.id).exists():
                # User has already liked, so unlike
                feedback.likes.remove(request.user)
                liked = False
            else:
                # User hasn't liked yet, so like
                feedback.likes.add(request.user)
                liked = True

            # Return a JSON response with the updated like status and count
            return JsonResponse({'liked': liked, 'likes_count': feedback.likes.count()})

    # Return a JsonResponse with an error message if the request is not valid
    return JsonResponse({'error': 'Invalid request'}, status=400)



def update_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            updated_property = form.save(commit=False)

            selected_features = form.cleaned_data['features']
            features_str = ', '.join(selected_features)
            updated_property.features = features_str

            selected_nearby_place = form.cleaned_data['nearby_place']
            nearby_place_str = ', '.join(selected_nearby_place)
            updated_property.nearby_place = nearby_place_str

            distance_to_major_road = input_and_average(form.cleaned_data['major_road'])
            distance_to_supermarket = input_and_average(form.cleaned_data['near_supermarket'])
            property_age = input_and_average(form.cleaned_data['building_age'])

            last_renovation_years_ago_input = form.cleaned_data['last_renovated']
            last_renovation_years_ago_parts = last_renovation_years_ago_input.split('-')
            last_renovation_years_ago = (int(last_renovation_years_ago_parts[0]) + int(last_renovation_years_ago_parts[1])) // 2

            property_type = form.cleaned_data['property_type']

            if property_type == 'Apartment':
                floor_value = form.cleaned_data['floor_no']
            else:
                floor_value = form.cleaned_data['floor']

            if property_type in ['Commercial', 'Garage']:
                num_bedrooms = 0
            else:
                num_bedrooms = form.cleaned_data['bedrooms']

            furnished = 1 if 'Furnished' in selected_features else 0
            air_conditioner = 1 if 'Air Condition' in selected_features else 0
            parking = 1 if 'Parking' in selected_features else 0
            water_available = 1 if 'Well(Water Availability)' in selected_features else 0

            user_input_dict = {
                'property_type': property_type,
                'num_bedrooms': num_bedrooms,
                'num_bathrooms': form.cleaned_data['bathrooms'],
                'furnished': furnished,
                'air_conditioner': air_conditioner,
                'parking': parking,
                'last_renovation_years_ago': last_renovation_years_ago,
                'water_available': water_available,
                'distance_to_major_road': [distance_to_major_road],
                'distance_to_supermarket': [distance_to_supermarket],
                'price': form.cleaned_data['price'],
                'property_age': [property_age],
                'total_rooms': form.cleaned_data['rooms'],
                'floor': floor_value
            }

            user_input_df = pd.DataFrame(user_input_dict)

            for col, le in label_encoders.items():
                user_input_df[col] = le.transform(user_input_df[col])

            sale_duration_prediction = model.predict(user_input_df)

            # Save the exact number of days to sell
            exact_days_to_sell = int(sale_duration_prediction[0])
            updated_property.days_to_sell = exact_days_to_sell

            # Generate property tips based on business logic
            property_tips = []

            if exact_days_to_sell > 30:
                property_tips = analyze_property_details(user_input_df.iloc[0])

            # Save property_tips
            updated_property.property_tips = ", ".join(property_tips)

            sale_duration_tips = []

            # Generate sale_duration_tips
            if exact_days_to_sell <= 30:
                sale_duration_tips.append("Your property is likely to sell quickly. Ensure it's well-maintained for a smooth sale.")
            elif exact_days_to_sell <= 60:
                sale_duration_tips.append("Your property may take a couple of months to sell. Consider staging and effective marketing.")
            else:
                sale_duration_tips.append("Your property may take some time to sell. Focus on competitive pricing and marketing strategies")

            # Set the sale_duration_tips field
            updated_property.sale_duration_tips = ", ".join(sale_duration_tips)

            updated_property.save()

            images = request.FILES.getlist('images')
            if images:
                # Delete existing property images and add new ones
                Image.objects.filter(property=updated_property).delete()
                for image in images:
                    property_image = Image(property=updated_property, images=image)
                    property_image.save()

            return redirect(reverse('property_single', args=[property_id]))
    else:
        form = PropertyForm(instance=property)

    return render(request, 'update_property.html', {'form': form, 'property': property })

def renForm(request):
    property_types = Property.objects.values_list('property_type', flat=True).distinct()
    return render(request,'Rental Form.html',{'property_types': property_types})



from django.shortcuts import render
from .forms import MortgageCalculatorForm

def mortgage_calculator(request):
    if request.method == 'POST':
        property_price = float(request.POST.get('property_price'))
        down_payment = float(request.POST.get('down_payment'))
        interest_rate = float(request.POST.get('interest_rate')) / 100
        loan_term_years = int(request.POST.get('loan_term_years'))
        
        principal = property_price - down_payment
        monthly_interest_rate = interest_rate / 12
        num_payments = loan_term_years * 12
        monthly_payment = (principal * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -num_payments)
        
        return render(request, 'mortgage_calculator.html', {'monthly_payment': monthly_payment})
    else:
        return render(request, 'mortgage_calculator.html')


from .models import LoanApplicant, Nominee

def home_loan_application(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        monthly_income = request.POST.get('monthly_income')
        loan_amount = request.POST.get('loan_amount')
        property_buying_city = request.POST.get('property_buying_city')
        email = request.POST.get('email')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        employment_type = request.POST.get('employment_type')
        ongoing_emi = request.POST.get('ongoing_emi')
        
        applicant = LoanApplicant.objects.create(
            user=request.user,
            name=name,
            monthly_income=monthly_income,
            loan_amount=loan_amount,
            property_buying_city=property_buying_city,
            email=email,
            age=age,
            gender=gender,
            employment_type=employment_type,
            ongoing_emi=ongoing_emi
        )
        
        # If credit score is provided
        if request.POST.get('credit_score_option') == 'Yes':
            credit_score = request.POST.get('credit_score')
            applicant.credit_score = credit_score
            applicant.save()
        
        # If nominee details are provided
        if request.POST.get('has_nominee'):
            nominee_name = request.POST.get('nominee_name')
            relationship = request.POST.get('relationship')
            phone_number = request.POST.get('phone_number')
            nominee_email = request.POST.get('nominee_email')
            
            nominee = Nominee.objects.create(
                applicant=applicant,
                name=nominee_name,
                relationship=relationship,
                phone_number=phone_number,
                nominee_email=nominee_email
            )
        
        send_email(name, email)  # Corrected this line
        return render(request, 'application_success.html')
    return render(request, 'home_loan_application.html')


def send_email(name, email):
    subject = 'Thank you for sharing your details! - FindMyNest'
    message = f"Congratulations, {name}! Your application is on its way.\n\n"
    message += "You've successfully completed your home loan application.\n\n"
    message += "We'll contact you shortly to discuss your best offers and guide you through the next steps.\n\n"
    
    from_email = 'findmynest.info@gmail.com'  # Replace with your actual email
    recipient_list = [email]
    
    send_mail(subject, message, from_email, recipient_list)
    

from .models import HomeInteriors

def home_interiors_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        city = request.POST.get('city')
        vendor = request.POST.get('vendor')
        budget = request.POST.get('budget')
        scope = request.POST.get('scope')
        apartment_type = request.POST.get('apartment_type')
        possession_timeline = request.POST.get('possession_timeline')
        comments = request.POST.get('comments')
        agreement = request.POST.get('agreement') == 'on'
        
        

        # Create a new HomeInteriors object
        home_interiors = HomeInteriors.objects.create(
            user=request.user,
            name=name,
            phone=phone,
            email=email,
            city=city,
            vendor=vendor,
            budget=budget,
            scope=scope,
            apartment_type=apartment_type,
            possession_timeline=possession_timeline,
            comments=comments,
            agreement=agreement
        )

        # Save the object to the database
        home_interiors.save()

        return render(request, 'application_success.html')  # Render to a success page after form submission
    else:
        return render(request, 'home_ Interiors.html')  # Render the form template for GET requests
    




def add_to_compare(request, property_id):
    # Retrieve the property object
    property_obj = get_object_or_404(Property, pk=property_id)

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Get or create CompareProperty object for the user
        compare_property, created = CompareProperty.objects.get_or_create(user=request.user)

        # Check if the property is already in the compare list
        if property_obj in compare_property.properties.all():
            messages.error(request, "This property is already in your compare list.")
        elif compare_property.properties.count() >= 4:
            messages.error(request, "You can only compare up to 4 properties.")
        else:
            # Add the property to the compare list
            compare_property.properties.add(property_obj)
            messages.success(request, "Property added to compare list successfully.")
    else:
        messages.error(request, "You need to be logged in to add properties to compare list.")

    return redirect('property_single', property_id=property_id)

def compare_properties(request):
    # Get the CompareProperty objects for the logged-in user
    compare_properties = CompareProperty.objects.filter(user=request.user)

    context = {'compare_properties': compare_properties}

    return render(request, 'compare_properties.html', context)


def remove_property(request, property_id):
    try:
        user = request.user
        compare_property = CompareProperty.objects.get(user=user)
        property_to_remove = compare_property.properties.get(id=property_id)
        compare_property.properties.remove(property_to_remove)
        return redirect(reverse('compare_properties'))  # Redirect to another view after removal
    except CompareProperty.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'CompareProperty not found'})
    except Property.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Property not found'})