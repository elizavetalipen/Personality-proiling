from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Field, Row, Column, HTML
from django.contrib.auth.models import User
from .models import UserProfile, Prediction


# форма для редактирования информации в профиле
class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['date_of_birth', 'avatar', 'about']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Field('date_of_birth', css_class='form-control'),
            Field('avatar', css_class='form-control-file'),
            Field('about', css_class='form-control'),
        )


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'password']
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.fields['password'].widget = forms.PasswordInput()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Div(
            Field('email', css_class='form-control col-md-6'),
            Field('password', css_class='form-control col-md-6'),
            css_class='form-group'
            )
        )


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Register'))

        self.helper.layout = Layout(
            Div(
                Field('username', css_class='form-control col-md-6'),
                Field('email', css_class='form-control col-md-6'),
                css_class='form-group'
            ),
            Div(
                Field('password1', css_class='form-control col-md-6'),
                Field('password2', css_class='form-control col-md-6'),
                css_class='form-group'
            )
        )


class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Login'))

        self.helper.layout = Layout(
            Div(
                Field('username', css_class='form-control col-md-6'),
                css_class='form-group'
            ),
            Div(
                Field('password', css_class='form-control col-md-6'),
                css_class='form-group'
            )
        )
        

class AddPredictionForm(forms.Form):
    input_link = forms.CharField(
        label='Input text', 
        max_length=600, 
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})  
    )
    file_upload = forms.FileField(label='Upload File', required=False)

    def __init__(self, *args, **kwargs):
        super(AddPredictionForm, self).__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit', css_class='btn btn-primary btn-sm'))
        
        self.helper.layout = Layout(
            Div(
                Field('input_link', css_class='form-control col-md-4'),
                css_class='form-group'
            ),
            Div(
                Field('file_upload', css_class='form-control col-md-4'),
                css_class='form-group'
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        input_link = cleaned_data.get('input_link')
        file_upload = cleaned_data.get('file_upload')

        # Check if both input_link and file_upload are empty
        if not input_link and not file_upload:
            raise forms.ValidationError("Please provide either input text or upload a file.")
        
        return cleaned_data



