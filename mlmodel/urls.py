from django.urls import path
from .views import *

urlpatterns = [
    path('', homepage_view, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('profile/settings/', profile_settings_view, name='profile_settings'),
    path('predict/',predict_view, name='predict'),
    path('error_page/', handle_exceptions, name="handle_exceptions"),
    path('save-to-pdf/', save_to_pdf, name='save_to_pdf'),
    path('save-to-history/', save_to_history, name='save_to_history'),
    path('delete_prediction/<int:prediction_id>/', delete_prediction, name='delete_prediction'),
]
