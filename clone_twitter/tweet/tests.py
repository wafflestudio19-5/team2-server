from django.test import TestCase

from factory.django import DjangoModelFactory

from user.models import User
from tweet.models import Tweet, Reply, Retweet
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


class RetweetFactory(DjangoModelFactory):
    class Meta:
        model = Retweet

    @classmethod
    def create(cls, **kwargs):
        retweet = Retweet.objects.create(**kwargs)
        retweet.save()
        return retweet


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
        # No content nor media
        data = self.post_data.copy()
        data.pop('content')
        # data.pop('media')
        response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_tweet_success(self):
        # there are both content and media
        data = self.post_data.copy()
        response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully write tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)

        # # there is only media
        # data.pop('content')
        # response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #
        # tweet_count = Tweet.objects.count()
        # self.assertEqual(tweet_count, 2)
        #
        # # there is only content
        # data = self.post_data.copy()
        # data.pop('media')
        # response = self.client.post('/api/v1/tweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #
        # tweet_count = Tweet.objects.count()
        # self.assertEqual(tweet_count, 3)


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
        tweets = Tweet.objects.all()
        tweet = tweets[0]
        retweet = tweets[1]
        response = self.client.delete('/api/v1/tweet/', data={'id': tweet.id}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete('/api/v1/tweet/', data={'id': retweet.id}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_tweet_wrong_id(self):
        response = self.client.delete('/api/v1/tweet/', data={'id': -1}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete('/api/v1/tweet/', data={'wrong': 'a'}, content_type='application/json', HTTP_AUTHORIZATION=self.other_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_tweet_success(self):
        tweets = Tweet.objects.all()
        tweet = tweets[0]
        retweet = tweets[1]
        response = self.client.delete('/api/v1/tweet/', data={'id': tweet.id}, content_type='application/json', HTTP_AUTHORIZATION=self.author_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete('/api/v1/tweet/', data={'id': retweet.id}, content_type='application/json', HTTP_AUTHORIZATION=self.author_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['message'], "successfully delete tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)


class ReplyTestCase(TestCase):

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

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        tweets = Tweet.objects.all()
        cls.tweet = tweets[0]

        cls.post_data = {
            'id': cls.tweet.id,
            'content': 'content',
            # 'media': 'media',
        }

    def test_reply_wrong_id(self):
        data = self.post_data.copy()
        data['id'] = -1
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reply_missing_required_field(self):
        # No tweet_id
        data = self.post_data.copy()
        data.pop('id')
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # No content nor media
        data = self.post_data.copy()
        data.pop('content')
        # data.pop('media')
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_tweet_success(self):
        # there are both content and media
        data = self.post_data.copy()
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully reply tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 2)
        reply_count = Reply.objects.count()
        self.assertEqual(reply_count, 1)

        # # there is only media
        # data.pop('content')
        # response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #
        # tweet_count = Tweet.objects.count()
        # self.assertEqual(tweet_count, 3)
        # reply_count = Reply.objects.count()
        # self.assertEqual(reply_count, 2)
        #
        # # there is only content
        # data = self.post_data.copy()
        # data.pop('media')
        # response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #
        # tweet_count = Tweet.objects.count()
        # self.assertEqual(tweet_count, 4)
        # reply_count = Reply.objects.count()
        # self.assertEqual(reply_count, 3)

    def test_reply_delete(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/reply/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        # delete replied tweet
        response = self.client.delete('/api/v1/tweet/', data={'id': self.tweet.id}, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        reply_count = Reply.objects.count()
        self.assertEqual(reply_count, 1)

        # delete replying tweet
        response = self.client.delete('/api/v1/tweet/', data={'id': self.tweet.id + 1}, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)
        reply_count = Reply.objects.count()
        self.assertEqual(reply_count, 0)


class RetweetTestCase(TestCase):

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

        cls.tweet = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user,
            content = 'content'
        )

        tweets = Tweet.objects.all()
        cls.tweet = tweets[0]

        cls.post_data = {
            'id': cls.tweet.id,
        }

    def test_retweet_wrong_id(self):
        data = self.post_data.copy()
        data['id'] = -1
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retweet_missing_required_field(self):
        # No tweet_id
        data = self.post_data.copy()
        data.pop('id')
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retweet_success(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['message'], "successfully do retweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 2)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 1)

    def test_retweet_multiple_times(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        with transaction.atomic():
            response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        data = response.json()
        self.assertEqual(data['message'], "you already retweeted this tweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 2)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 1)

    def test_retweet_delete(self):
        data = self.post_data.copy()
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        # delete retweeting tweet
        response = self.client.delete('/api/v1/tweet/', data={'id': self.tweet.id + 1}, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 0)

        # delete retweeted tweet
        data = self.post_data.copy()
        response = self.client.post('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        response = self.client.delete('/api/v1/tweet/', data={'id': self.tweet.id}, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 0)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 0)


class RetweetCancelTestCase(TestCase):

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
            author = cls.user,
            content = 'content'
        )

        cls.retweeting = TweetFactory(
            tweet_type = 'RETWEET',
            author = cls.user,
            content = 'content',
            retweeting_user = cls.user.user_id
        )

        cls.retweet = RetweetFactory(
            retweeted = cls.tweet,
            retweeting = cls.retweeting,
            user = cls.user
        )

        tweets = Tweet.objects.all()
        cls.source_tweet = tweets[0]

        cls.post_data = {
            'source_id': cls.source_tweet.id,
        }

    def test_retweet_cancel_wrong_source_id(self):
        data = self.post_data.copy()
        data['source_id'] = -1
        response = self.client.delete('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retweet_cancel_missing_required_field(self):
        # No source_id
        data = self.post_data.copy()
        data.pop('source_id')
        response = self.client.delete('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data['message'], "you have specify source tweet you want to cancel retweet")

    def test_retweet_cancel_does_not_exist_retweet(self):
        response = self.client.delete('/api/v1/tweet/', data={'id': self.source_tweet.id + 1}, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)

        data = self.post_data.copy()
        response = self.client.delete('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertEqual(data['message'], "you have not retweeted this tweet")

    def test_retweet_cancel_success(self):
        data = self.post_data.copy()
        response = self.client.delete('/api/v1/retweet/', data=data, content_type='application/json', HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['message'], "successfully cancel retweet")

        tweet_count = Tweet.objects.count()
        self.assertEqual(tweet_count, 1)
        retweet_count = Retweet.objects.count()
        self.assertEqual(retweet_count, 0)