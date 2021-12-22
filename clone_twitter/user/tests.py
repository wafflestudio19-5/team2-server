from django.test import TestCase

from factory.django import DjangoModelFactory

from user.models import User, Follow
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
        cls.user = UserFactory(
            email='email@email.com',
            user_id='user1_id',
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
        data = {'user_id': 'user1_id', 'password': 'password'}
        response = self.client.post('/api/v1/login/', data=data, content_type='application/json',
                                   HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["token"], jwt_token_of(User.objects.get(user_id='user1_id')))

class PostFollowTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.user2 = UserFactory(
            email='email2@email.com',
            user_id='user2_id',
            username='username2',
            password='password',
            phone_number='010-1234-0000'
        )
        cls.user2_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.user3 = UserFactory(
            email='email3@email.com',
            user_id='user3_id',
            username='username3',
            password='password',
            phone_number='010-0000-0000'
        )
        cls.user3_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        Follow.objects.create(follower=cls.user1, following=cls.user2)

    def test_post_follow_fail(self):
        # target user does not exist
        response = self.client.post(
            '/api/v1/follow/',
            data={'user_id': 'invalid user'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # trying to follow oneself
        response = self.client.post(
            '/api/v1/follow/',
            data={'user_id': 'user1_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # trying to follow already following user
        response = self.client.post(
            '/api/v1/follow/',
            data={'user_id': 'user2_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_post_follow_success(self):
        response = self.client.post(
            '/api/v1/follow/',
            data={'user_id': 'user3_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


