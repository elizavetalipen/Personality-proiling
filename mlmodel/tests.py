from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import UserProfile, Prediction
from .forms import UserProfileEditForm, UserEditForm, AddPredictionForm
from datetime import datetime


class UserAuthTest(TestCase):
    ''' Test login, registration and restricted access'''

    def setUp(self):
        self.user = User.objects.create_user(
            username='usrtst',
            password='testpassw',
            email='test@gmail.com',
        )

    def test_login(self):
        url = reverse('login')
        response = self.client.post(url, {'username': 'usrtst', 'password': 'testpassw'})
        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, reverse('home'))


    def test_logout(self):
        url = reverse('logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, reverse('login'))


    def test_register(self):
        url = reverse('register')
        response = self.client.post(url, {
            'username': 'newusr',
            'email': 'newuser@gmail.com',
            'password1': 'newpassw',
            'password2': 'newpassw',
        })
        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, reverse('home'))


    def test_unauthorized_access(self):
        urls = [reverse('profile'), reverse('edit_profile'), reverse('profile_settings')]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, f'/accounts/login/?next={url}')



class UserProfileTest(TestCase):
    ''' Tests editing profile info and settings'''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='usrtst', password='testpassw')
        self.user_profile = UserProfile.objects.create(user=self.user,
            date_of_birth=None, avatar='unnamed.jpg', 
            about='This is the profile description', count=0)


    def test_edit_profile(self):
        self.client.login(username='usrtst', password='testpassw')
        form_data = {
            'date_of_birth': '1999-02-02',
            'avatar': 'unnamed.jpg',
            'about': 'And this is the updated profile description', 'count':'0'}
        response = self.client.post(reverse('edit_profile'), data=form_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userprofile/profile.html')
        self.user_profile.refresh_from_db()
        self.assertEqual(str(self.user_profile.date_of_birth), form_data['date_of_birth'])
        self.assertEqual(self.user_profile.avatar.name, form_data['avatar'])
        self.assertEqual(self.user_profile.about, form_data['about'])


    def test_edit_settings(self):
        self.client.login(username='usrtst', password='testpassw')
        form_data = {'email': 'newemail@gmail.com','password': 'newtestpasw'}
        response = self.client.post(reverse('profile_settings'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userprofile/profile.html')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, form_data['email'])
        self.assertTrue(self.user.check_password(form_data['password']))

    def tearDown(self):
        self.user.delete()
        self.user_profile.delete()


class PredictViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='usrtst', password='testpassw')
        self.user_profile = UserProfile.objects.create(user=self.user,
            date_of_birth=None, avatar='unnamed.jpg', 
            about='This is the profile description', count=0)
        self.client.login(username='usrtst', password='testpassw')

    def test_get_request(self):
        self.client.login(username='usrtst', password='testpassw')
        response = self.client.get(reverse('predict'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predict_revenue.html')


    def test_make_prediction(self):
        self.client.login(username='usrtst', password='testpassw')
        form_data = {'city': 'Bursa','city_group': 'Other',
            'type': 'IL','date': '2022-05-12',
            'P2': 1,'P6': 2,
            'P23': 3,'P28': 4}
        response = self.client.post(reverse('predict'), data=form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predict_revenue.html')
        self.assertContains(response, 'prediction')
        self.assertIsInstance(response.context['form'], AddPredictionForm)

        prediction = Prediction.objects.filter(user=self.user).last()
        self.assertEqual(prediction.predicted_revenue, response.context['prediction'])
        self.assertEqual(prediction.user, self.user)

        user_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(user_profile.count, 1)

    def tearDown(self):
        self.user.delete()
        self.user_profile.delete()



