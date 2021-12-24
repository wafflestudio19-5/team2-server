from django.test import TestCase

from factory.django import DjangoModelFactory

from user.models import User
from django.test import TestCase
from django.db import transaction
from rest_framework import status
from user.serializers import jwt_token_of

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = 'test@test.com'

    @classmethod
    def create(cls, **kwargs):
        user = User.objects.create(**kwargs)
        user.set_password(kwargs.get('password', ''))
        user.save()
        return user

# Create your tests here.
class PostUserTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )

        cls.post_data = {
            'email': 'email@email.com',
            'user_id': 'bake_waffle',
            'username': 'waffle',
            'password': 'password',
        }

    def test_post_user_already_exists(self):
        data = self.post_data
        with transaction.atomic():
           response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_missing_required_field(self):
        data = self.post_data.copy()
        data.pop('email')
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = self.post_data.copy()
        data.pop('user_id')
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_invalid_phone_number(self):
        data = self.post_data.copy()
        data.update({'email': 'valid@email.com', 'phone_number': 'invalid'})
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_success(self):
        data = {
            'email': 'success@email.com',
            'user_id': 'success',
            'username': 'waffle',
            'password': 'password',
            'phone_number': '010-9999-9999'
        }
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("token", data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 2)

class PostLoginTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.participant = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

    def test_post_user_login_auth_fail(self):
        # user does not exist -> Q.frontend..??

        # wrong password
        response = self.client.post(
            '/api/v1/login/',
            data={'user_id': 'user_id', 'password': 'wrongpassword'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_user_login_success(self):
        data = {'user_id': 'user_id', 'password': 'password'}
        response = self.client.post('/api/v1/login/', data=data, content_type='application/json',
                                   HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["token"], jwt_token_of(User.objects.get(user_id='user_id')))

