from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import update_session_auth_hash
from .forms import RegistrationForm, LoginForm
from django.contrib.auth.decorators import login_required
from .forms import UserProfileEditForm, UserEditForm, AddPredictionForm
from .models import UserProfile, Prediction
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .utils import *
from django.utils import timezone
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from django.conf import settings
import json
from PyPDF2 import PdfFileWriter, PdfFileReader
import logging
from .exceptions import NotFoundError, ValidationError
from datetime import datetime
import os


logger = logging.getLogger(__name__)

def handle_exceptions(view_func):
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except (NotFoundError, ValidationError) as e:
            logger.exception(f"{type(e).__name__}: {str(e)} at {datetime.now()}")
            return render(request, 'error_page.html', {'status_code': e.status_code, 'error_message': e.error_message})
        except Exception as e:
            logger.exception(f"{type(e).__name__}: {str(e)} at {datetime.now()}")
            return render(request, 'error_page.html', {'status_code': 500, 'error_message': 'Internal Server Error'})
    return wrapper


@handle_exceptions
def homepage_view(request):
    return render(request, 'home.html')


@handle_exceptions
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            user_profile = UserProfile.objects.create(user=user, date_of_birth=None, 
                                                 avatar='images/userdata/unnamed.jpg', about='...', count=0)
            logger.info(f'New user {username} registered at {datetime.now()}')
            return redirect('/')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@handle_exceptions
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info(f'User {username} logged in at {datetime.now()}')
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


@handle_exceptions
def logout_view(request):
    logout(request)
    return redirect('home')


@handle_exceptions
@login_required
def profile_view(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    predictions = Prediction.objects.filter(user=user).order_by('-prediction_date')
    return render(request, 'userprofile/profile.html', {
        'user_profile': user_profile,
        'predictions': predictions,
    })


@handle_exceptions
@login_required
def edit_profile_view(request):
    
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            logger.info(f'User {request.user.username} edited profile at {datetime.now()}')
            return redirect('profile')
    else:
        form = UserProfileEditForm(instance=user_profile)
    return render(request, 'userprofile/edit_profile.html', {'form': form})


@handle_exceptions
@login_required
def profile_settings_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data['password']
            if new_password:
                user.set_password(new_password)
            user.save()
            logger.info(f'User {user.username} changed profile settings at {datetime.now()}')
            update_session_auth_hash(request, user)
            return redirect('profile')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'userprofile/settings_profile.html', {'form': form})


@login_required
@handle_exceptions
def save_to_history(request):
    if request.method == 'POST':
        description = request.POST.get('description', '') 
        final_result = request.POST.get('mbti_type', '') 

        if final_result and description:  
            prediction = Prediction(
                user=request.user,
                prediction_date=timezone.now(),
                final_result=final_result,
                description=description
            )
            try:
                prediction.save() 
                user_profile = UserProfile.objects.get(user=request.user)
                user_profile.count += 1
                user_profile.save()
                
                messages.success(request, "Prediction was saved to profile history.")
            except Exception as e:
                messages.error(request, "An error occurred while saving the prediction.")
        else:
            messages.warning(request, "Invalid input data.")
        
        return redirect('predict')
    
    return redirect('predict')


@handle_exceptions
def save_to_pdf(request):
    try:
        image_name = request.POST.get('image_name')
        quote = request.POST.get('quote')
        prediction = request.POST.get('prediction')
        link = request.POST.get('link')
        image_name = image_name.replace('/', '\\')
        image_name = image_name.replace('media', '')
        full_image_path = settings.MEDIA_ROOT + image_name

        context = {
            'image_name': full_image_path,
            'quote': quote,
            'prediction': prediction,
            'link': link,
        }

        html_content = render_to_string('file_section.html', context)
        pdf_file = BytesIO()
        result = pisa.CreatePDF(html_content, dest=pdf_file)

        if result.err:
            raise Exception("PDF generation failed")

        response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="section.pdf"'

        return response

    except Exception as e:
        messages.error(request, "An error occurred while generating the PDF. Please try again later.")
        return redirect('predict')
    
    
@login_required
@handle_exceptions
def delete_prediction(request, prediction_id):
    if request.method == 'POST':
        prediction = get_object_or_404(Prediction, id=prediction_id)
    
        if prediction.user == request.user:
            prediction.delete()
            messages.success(request, "Prediction deleted successfully.")
        else:
            messages.error(request, "You are not authorized.")
    
    return redirect('profile')


@handle_exceptions
def predict_view(request):
    user = request.user
    prediction = "Discover your personality type."
    image_name = f"{settings.MEDIA_URL}images/types_pics/default.jpg"
    quotes = quotes_dict
    file_content, input_text = "", ""
    form = AddPredictionForm(request.POST, request.FILES)  

    if request.method == 'POST':
        
        if form.is_valid():
            # если загружаем файл
            if 'file_upload' in request.FILES:
                
                uploaded_file = request.FILES['file_upload']
                file_content = read_text_from_file(uploaded_file)
                form = AddPredictionForm(initial={'input_file':uploaded_file,
                    'input_link': file_content})

            else:
                input_text = request.POST.get('input_link', '') 
                # предсказанный тип личности
                mbti_type = make_prediction(input_text)
                
                # на основании него подбираются описание и картинка
                image_name = f"{settings.MEDIA_URL}images/types_pics/{mbti_type}.jpg"
                quote = quotes.get(mbti_type, "")
                link = f'https://www.16personalities.com/{mbti_type}-personality'
                prediction = descriptions_dict.get(mbti_type, "")
                
                # дополнительно анализ тональности 
                emotion_analysis = sentiment_analysis(input_text)
                linguistic_analysis = ling_analysis(input_text)
                
                context = {'form': form,'prediction': prediction,
                          'mbti_type': mbti_type,'image_name': image_name,
                          'quote': quote,'link': link,
                          'emotion_analysis': emotion_analysis,
                          'linguistic_analysis': linguistic_analysis}

                return render(request, 'predict_type.html', context)
        else:
            print(form.errors)
    else:
        form = AddPredictionForm()

    return render(request, 'predict_type.html', {'form': form, 'prediction': prediction,'image_name': image_name}) 






