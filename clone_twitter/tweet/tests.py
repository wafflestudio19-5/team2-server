from django.test import TestCase

from factory.django import DjangoModelFactory

from user.models import User
from tweet.models import Tweet
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


class TweetFactory(DjangoModelFactory):
    class Meta:
        model = Tweet
    id = 1

    @classmethod
    def create(cls, **kwargs):
        tweet = Tweet.objects.create(**kwargs)
        tweet.save()
        return tweet


class PostTweetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.post_data = {
            'content': 'content',
            # 'media': 'media',
        }

    def test_post_tweet_missing_required_field(self):
        data = self.post_data.copy()
        data.pop('content')
        response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_tweet_success(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("successfully write tweet", data)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)


class DeleteTweetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.author = UserFactory(
            email='email@email.com',
            user_id='user_id',
            username='username',
            password='password',
            phone_number='010-1234-5678'
        )
        cls.author_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.other = UserFactory(
            email='test@email.com',
            user_id='other',
            username='username1',
            password='password',
            phone_number='010-1111-2222'
        )
        cls.other_token = 'JWT ' + jwt_token_of(User.objects.get(email='test@email.com'))

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.author,
            content = 'content'
        )

        cls.retweet = TweetFactory(
            tweet_type = 'RETWEET',
            author = cls.other,
            retweeting_user = cls.author.user_id,
            content = 'content'
        )

    def test_delete_not_my_tweet(self):
        response = self.client.delete('/api/v1/tweet/', data={'id': 1}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete('/api/v1/tweet/', data={'id': 2}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_tweet_wrong_id(self):
        response = self.client.delete('/api/v1/tweet/', data={'id': 3}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.delete('/api/v1/tweet/', data={'wrong': 'a'}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_tweet_success(self):
        response = self.client.delete('/api/v1/tweet/', data={'id': 1}, content_type='application/json', HTTP_AUTHORIZATION=self.author_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete('/api/v1/tweet/', data={'id': 2}, content_type='application/json', HTTP_AUTHORIZATION=self.author_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("successfully delete tweet", data)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)