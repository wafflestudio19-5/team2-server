import datetime
from django.db.models import query
from django.test import TestCase

from factory.django import DjangoModelFactory
from tweet.models import Retweet, Tweet

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
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 1)
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
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 2)

class DeleteUnfollowTestCase(TestCase):

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
        Follow.objects.create(follower=cls.user1, following=cls.user2)

    def test_delete_unfollow_fail(self):
        response = self.client.delete(
            '/api/v1/unfollow/',
            data={'user_id': 'invalid_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(
            '/api/v1/unfollow/',
            data={'user_id': 'user3_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 1)

    def test_delete_unfollow_success(self):
        response = self.client.delete(
            '/api/v1/unfollow/',
            data={'user_id': 'user2_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 0)

    def test_unfollow_and_refollow(self):
        self.client.delete(
            '/api/v1/unfollow/',
            data={'user_id': 'user2_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        response = self.client.post(
            '/api/v1/follow/',
            data={'user_id': 'user2_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 1)

class GetFollowListTestCase(TestCase):

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

        cls.user3 = UserFactory(
            email='email3@email.com',
            user_id='user3_id',
            username='username3',
            password='password',
            phone_number='010-0000-0000'
        )
        Follow.objects.create(follower=cls.user1, following=cls.user2)
        Follow.objects.create(follower=cls.user2, following=cls.user1)
        Follow.objects.create(follower=cls.user3, following=cls.user1)

    def test_get_follower_success(self):
        response = self.client.get(
            '/api/v1/follow_list/3/follower/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_following_success(self):
        response = self.client.get(
            '/api/v1/follow_list/3/following/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GetRecommendTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username',
            password='password',
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.user2 = UserFactory(
            email='email2@email.com',
            user_id='user2_id',
            username='username2',
            password='password',
        )

        cls.user3 = UserFactory(
            email='email3@email.com',
            user_id='user3_id',
            username='username3',
            password='password',
        )
        cls.user3_token = 'JWT ' + jwt_token_of(User.objects.get(email='email3@email.com'))

        cls.user4 = UserFactory(
            email='email4@email.com',
            user_id='user4_id',
            username='username4',
            password='password',
        )

        cls.user5 = UserFactory(
            email='email5@email.com',
            user_id='user5_id',
            username='username5',
            password='password',
        )

        cls.user6 = UserFactory(
            email='email6@email.com',
            user_id='user6_id',
            username='username6',
            password='password',
        )
        Follow.objects.create(follower=cls.user1, following=cls.user2)
        Follow.objects.create(follower=cls.user2, following=cls.user1)
        Follow.objects.create(follower=cls.user3, following=cls.user1)
        Follow.objects.create(follower=cls.user3, following=cls.user4)
        Follow.objects.create(follower=cls.user3, following=cls.user6)
        Follow.objects.create(follower=cls.user5, following=cls.user1)
        Follow.objects.create(follower=cls.user5, following=cls.user2)
        Follow.objects.create(follower=cls.user5, following=cls.user3)
        Follow.objects.create(follower=cls.user5, following=cls.user4)
        Follow.objects.create(follower=cls.user5, following=cls.user6)

    def test_get_recommend_success(self):
        response = self.client.get(
            '/api/v1/recommend/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data[0]['user_id'], "user3_id")
        self.assertEqual(data[1]['user_id'], "user4_id")
        self.assertEqual(data[2]['user_id'], "user5_id")

    def test_get_recommend_empty(self):
        response = self.client.get(
            '/api/v1/recommend/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user3_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['message'], "not enough users to recommend")

    def test_get_recommend_fail(self):
        # unauthorized
        response = self.client.get(
            '/api/v1/recommend/',
            data={},
            content_type='application/json',)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_follow_recommend_success(self):
        response = self.client.get(
            '/api/v1/follow/10/recommend/',   # user 5's pk : 10
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data[0]['user_id'], "user3_id")
        self.assertEqual(data[1]['user_id'], "user4_id")
        self.assertEqual(data[2]['user_id'], "user6_id")


class GetUserProfileTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username',
            password='password',
            phone_number='010-1234-5678',
            bio='I am User 1.',
            birth_date=datetime.date(2002, 11, 15)
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))
    
        cls.user2 = UserFactory(
            email='email2@email.com',
            user_id='user2_id',
            username='username2',
            password='password',
            phone_number='010-2345-6789',
            bio='', # blank
            birth_date=None # null
        )
        cls.user2_token = 'JWT ' + jwt_token_of(User.objects.get(email='email2@email.com'))

        cls.static_response_user1 = {
            'username' : 'username',
            'bio': 'I am User 1.',
            'birth_date': '2002-11-15'
        }

        cls.static_response_user2 = {
            'username' : 'username2',
            'bio': '',
            'birth_date': None
        }

    def test_get_profile_nonexistent_user(self):
        response = self.client.get(
            '/api/v1/user/user4_id/profile/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_profile_success(self):

        # get user's own profile
        response = self.client.get(
            '/api/v1/user/me/profile/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_user1['username'])
        self.assertEqual(data['bio'], self.static_response_user1['bio'])
        self.assertEqual(data['birth_date'], self.static_response_user1['birth_date'])

        # get other user's profile with blank data and null data
        response = self.client.get(
            '/api/v1/user/user2_id/profile/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_user2['username'])
        self.assertEqual(data['bio'], self.static_response_user2['bio'])
        self.assertEqual(data['birth_date'], self.static_response_user2['birth_date'])

class PatchUserProfileTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username',
            password='password',
            phone_number='010-1234-5678',
            bio='I am User 1.',
            birth_date=datetime.date(2002, 11, 15)
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.static_response_patch1 = {
            'username' : 'username2',
            'bio': 'I am User 2.',
            'birth_date': '2006-10-18'
        }

        cls.static_response_patch2 = {
            'username' : 'username2',
            'bio': '',
            'birth_date': None
        }


    # TODO include testcase with profile_img and header_img
    def test_patch_profile_success(self):
        # all profile data included
        response = self.client.patch(
            '/api/v1/user/profile/',
            data={
                'username': 'username2',
                'bio': 'I am User 2.',
                'birth_date': datetime.date(2006, 10, 18)
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_patch1['username'])
        self.assertEqual(data['bio'], self.static_response_patch1['bio'])
        self.assertEqual(data['birth_date'], self.static_response_patch1['birth_date'])

        # username unincluded & update data into blank or null
        response = self.client.patch(
            '/api/v1/user/profile/',
            data={
                'bio': '',
                'birth_date': None
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_patch2['username'])
        self.assertEqual(data['bio'], self.static_response_patch2['bio'])
        self.assertEqual(data['birth_date'], self.static_response_patch2['birth_date'])

class GetUserTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username',
            password='password',
            phone_number='010-1234-5678',
            bio='I am User 1.',
            birth_date=datetime.date(2002, 11, 15)
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))

        cls.user2 = UserFactory(
            email='email2@email.com',
            user_id='user2_id',
            username='username2',
            password='password',
            phone_number='010-2345-6789',
            bio='', # blank
            birth_date=None # null
        )
        cls.user2_token = 'JWT ' + jwt_token_of(User.objects.get(email='email2@email.com'))

        cls.user3 = UserFactory(
            email='email3@email.com',
            user_id='user3_id',
            username='username3',
            password='password',
            phone_number='010-3456-7890',
            bio='I am User 3.',
            birth_date=datetime.date(2006, 10, 18)
        )
        cls.user3_token = 'JWT ' + jwt_token_of(User.objects.get(email='email3@email.com'))

        cls.tweet1 = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user1,
            content = 'content1'
        )

        cls.tweet2 = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user1,
            content = 'content2'
        )

        cls.tweet3 = TweetFactory(
            tweet_type = 'GENERAL',
            author = cls.user3,
            content = 'content3'
        )

        cls.tweet4 = TweetFactory(
            tweet_type = 'RETWEET',
            author = cls.user3,
            retweeting_user = 'user1_id',
            content = 'content3'
        )

        cls.retweet = RetweetFactory(
            retweeted = cls.tweet3,
            retweeting = cls.tweet4,
            user = cls.user1
        )
        
        cls.static_response_user1 = {
            'username' : 'username',
            'user_id': 'user1_id',
            'bio': 'I am User 1.',
            'birth_date': '2002-11-15',
            'tweets_num': 3,
            'following': 2,
            'follower': 0
        }

        cls.static_response_user2 = {
            'username' : 'username2',
            'user_id': 'user2_id',
            'bio': '',
            'birth_date': None,
            'tweets_num': 0,
            'following': 0,
            'follower': 1
        }

        Follow.objects.create(follower=cls.user1, following=cls.user2)
        Follow.objects.create(follower=cls.user1, following=cls.user3)

    def test_get_info_nonexistent_user(self):
        response = self.client.get(
            '/api/v1/user/user4_id/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_info_success(self):
        response = self.client.get(
            '/api/v1/user/user1_id/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()

        self.assertEqual(data['username'], self.static_response_user1['username'])
        self.assertEqual(data['user_id'], self.static_response_user1['user_id'])
        self.assertEqual(data['bio'], self.static_response_user1['bio'])
        self.assertIn("created_at", data)
        self.assertEqual(data['birth_date'], self.static_response_user1['birth_date'])
        self.assertEqual(data['tweets_num'], self.static_response_user1['tweets_num'])
        self.assertEqual(data['following'], self.static_response_user1['following'])
        self.assertEqual(data['follower'], self.static_response_user1['follower'])

        # get info with blank data and null data
        response = self.client.get(
            '/api/v1/user/user2_id/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()

        self.assertEqual(data['username'], self.static_response_user2['username'])
        self.assertEqual(data['user_id'], self.static_response_user2['user_id'])
        self.assertEqual(data['bio'], self.static_response_user2['bio'])
        self.assertIn("created_at", data)
        self.assertEqual(data['birth_date'], self.static_response_user2['birth_date'])
        self.assertEqual(data['tweets_num'], self.static_response_user2['tweets_num'])
        self.assertEqual(data['following'], self.static_response_user2['following'])
        self.assertEqual(data['follower'], self.static_response_user2['follower'])

        # get user's own info
        response = self.client.get(
            '/api/v1/user/me/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_user1['username'])
        self.assertEqual(data['user_id'], self.static_response_user1['user_id'])
        self.assertEqual(data['bio'], self.static_response_user1['bio'])
        self.assertIn("created_at", data)
        self.assertEqual(data['birth_date'], self.static_response_user1['birth_date'])
        self.assertEqual(data['tweets_num'], self.static_response_user1['tweets_num'])
        self.assertEqual(data['following'], self.static_response_user1['following'])
        self.assertEqual(data['follower'], self.static_response_user1['follower'])

class PatchUserIDTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory(
            email='email@email.com',
            user_id='user1_id',
            username='username',
            password='password',
            phone_number='010-1234-5678',
            bio='I am User 1.',
            birth_date=datetime.date(2002, 11, 15)
        )
        cls.user1_token = 'JWT ' + jwt_token_of(User.objects.get(email='email@email.com'))
 
        cls.static_response_patch1 = {
            'username' : 'username',
            'user_id': 'user1',
            'bio': 'I am User 1.',
            'birth_date': '2002-11-15',
            'tweets_num': 0,
            'following': 0,
            'follower': 0
        }

        cls.static_response_patch2 = {
            'username' : 'username',
            'user_id': 'user2_ID',
            'bio': 'I am User 1.',
            'birth_date': '2002-11-15',
            'tweets_num': 0,
            'following': 0,
            'follower': 0
        }

    def test_patch_user_id_wrong_length(self):
        # too short
        response = self.client.patch(
            '/api/v1/user/id/',
            data={'user_id': 'use'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
 
        
        # too long
        response = self.client.patch(
            '/api/v1/user/id/',
            data={'user_id': 'useruseruseruser'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
 

    def test_patch_user_id_unallowed_letter(self):
        # whitespace is not allowed
        response = self.client.patch(
            '/api/v1/user/id/',
            data={'user_id': 'user1_ ID'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
 

    def test_patch_user_id_identical(self):
        # cannot change into identical user_id
        response = self.client.patch(
            '/api/v1/user/id/',
            data={'user_id': 'user1_id'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
 

    def test_patch_user_id_success(self):
        # alphabets & digits
        response = self.client.patch(
            '/api/v1/user/id/',
            data={'user_id': 'user1'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_patch1['username'])
        self.assertEqual(data['user_id'], self.static_response_patch1['user_id'])
        self.assertEqual(data['bio'], self.static_response_patch1['bio'])
        self.assertIn("created_at", data)
        self.assertEqual(data['birth_date'], self.static_response_patch1['birth_date'])
        self.assertEqual(data['tweets_num'], self.static_response_patch1['tweets_num'])
        self.assertEqual(data['following'], self.static_response_patch1['following'])
        self.assertEqual(data['follower'], self.static_response_patch1['follower'])

        # underscore(_) included
        response = self.client.patch(
            '/api/v1/user/id/',
            data={'user_id': 'user2_ID'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], self.static_response_patch2['username'])
        self.assertEqual(data['user_id'], self.static_response_patch2['user_id'])
        self.assertEqual(data['bio'], self.static_response_patch2['bio'])
        self.assertIn("created_at", data)
        self.assertEqual(data['birth_date'], self.static_response_patch2['birth_date'])
        self.assertEqual(data['tweets_num'], self.static_response_patch2['tweets_num'])
        self.assertEqual(data['following'], self.static_response_patch2['following'])
        self.assertEqual(data['follower'], self.static_response_patch2['follower'])

class GetSearchPeopleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):

        user_id_list = ['test0', 'test1', 'test2', 'test3', 'test4', 'test5', 'test6', 'test7', 'test8ee', 'test9', 'kk', 'tt']
        username_list = ['f', 'aa', 'f', 'aa', 'aabb', 'aabbcc', 'aabbcc', 'aabbcc', 'aabbcc', 'aabbcc', 'ee', 'gg']
        bio_list = ['', '', 'aabbcc', 'mol', '?', 'ru', '', 'aaccdd', 'aa', 'aabbccddee', '', '']
        follow_relation = [(0,8), (1,8), (0,6)]
        
        cls.users = [
            UserFactory(
                email='email%d@email.com' % i,
                user_id=user_id_list[i],
                username=username_list[i],
                password='password',
                phone_number='010-0000-%04d' % i,
                bio=bio_list[i],
                birth_date=None
            ) for i in range(len(user_id_list))]

        cls.tokens = ['JWT ' + jwt_token_of(User.objects.get(email='email%d@email.com' % i))
            for i in range(len(user_id_list))]

        for init, term in follow_relation:
            Follow.objects.create(follower=cls.users[init], following=cls.users[term])

    # Several Keywords without @ sign
    def test_get_search_people_without_atsign(self):
        response = self.client.get(                            
            '/api/v1/search/people/',
            {'query': r'bb cc aa dd ee'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.tokens[0])
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(map(lambda x:x['user_id'], response.json()['results'])),
        ['test9', 'test8ee', 'test7', 'test6', 'test5', 'test4', 'test1', 'test3', 'kk', 'test2'])

    # Several Keywords with those including @ sign
    def test_get_search_people_with_atsign(self):
        response = self.client.get(                            
            '/api/v1/search/people/',
            {'query': r'bb cc aa  dd @kk @tt ee'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.tokens[0])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(map(lambda x:x['user_id'], response.json()['results'])),
        ['kk', 'tt', 'test9', 'test8ee', 'test7', 'test6', 'test5', 'test4', 'test1', 'test3', 'test2'])