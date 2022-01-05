import json
from user.utils import unique_random_id_generator, unique_random_email_generator
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, permissions, viewsets
from rest_framework.views import Response, APIView
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.serializers import UserCreateSerializer, UserLoginSerializer, FollowSerializer, UserFollowSerializer, UserFollowingSerializer, jwt_token_of, UserRecommendSerializer
from django.db import IntegrityError
from django.db.models import Q
from user.models import Follow, User, SocialAccount
import requests
from twitter.settings import get_secret, FRONT_URL
# Create your views here.

class PingPongView(APIView):
    permission_classes = (permissions.AllowAny,)

    swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ping': openapi.Schema(type=openapi.TYPE_STRING, description='ping'),
        }
    ))

    def get(self, request):
        response = redirect(FRONT_URL)
        response['Authorization'] = "JWT " + "hah"
        return response
        return Response(data={'ping': 'pong'}, status=status.HTTP_200_OK)

class EmailSignUpView(APIView):   #signup with email
    permission_classes = (permissions.AllowAny, )
    # parser_classes = [JSONParser]

    @swagger_auto_schema(request_body=openapi.Schema(  #TODO check format
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='user_id'),
            'email': openapi.Schema(type=openapi.FORMAT_EMAIL, description='email'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='username'),
            'profile_img': openapi.Schema(type=openapi.TYPE_FILE, description='profile_img'),
            'header_img': openapi.Schema(type=openapi.TYPE_FILE, description='header_img'),
            'bio': openapi.Schema(type=openapi.TYPE_STRING, description='bio'),
            'birth_date': openapi.Schema(type=openapi.FORMAT_DATETIME, description='birth_date'),
        }
    ))

    def post(self, request, *args, **kwargs):

        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user, jwt_token = serializer.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT, data={"message": "unexpected db error"})
        return Response({'token': jwt_token, 'user_id': user.user_id}, status=status.HTTP_201_CREATED)

class UserLoginView(APIView): #login with user_id
    permission_classes = (permissions.AllowAny, )

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='user_id'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='password'),
        }
    ))

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        user_id = serializer.validated_data['user_id']
        return Response({'success': True, 'token': token, 'user_id': user_id}, status=status.HTTP_200_OK)

# TODO: Logout.. expire token and add blacklist.. ?

class UserFollowView(APIView): # TODO: refactor to separate views.. maybe using viewset
    permission_classes = (permissions.IsAuthenticated,)  # later change to Isauthenticated

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='user_id'),
        }
    ))

    def post(self, request):
        serializer = FollowSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            follow_relation = serializer.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT, data={'message':'user already follows followee'})
        return Response(status=status.HTTP_201_CREATED) #TODO: recommend user

class UserUnfollowView(APIView):
    permission_classes = (permissions.IsAuthenticated,)  # later change to Isauthenticated

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='user_id'),
        }
    ))

    def delete(self, request):
        target_id = request.data.get('user_id', None)
        if target_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message':'you have specify user you want to unfollow'})
        try:
            following = User.objects.get(user_id=target_id)
            follow_relation = Follow.objects.get(follower=request.user, following=following)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such user exists'})
        except Follow.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'you can unfollow only currently following user'})
        follow_relation.delete()
        return Response(status=status.HTTP_200_OK, data='successfully unfollowed')

class FollowListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = UserFollowSerializer
    # TODO: 1. common serializer based on user model & manually make user list OR 2. separate 2serializers based on follow
    permission_classes = (permissions.AllowAny,)

    # GET /api/v1/follow_list/{lookup}/follower/
    @action(detail=True, methods=['GET'])
    def follower(self, request, pk=None):
        user = get_object_or_404(User, user_id=pk)
        followers = Follow.objects.filter(following=user) # TODO: order?

        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /api/v1/follow_list/{lookup}/following/
    @action(detail=True, methods=['GET'])
    def following(self, request, pk=None):
        user = get_object_or_404(User, user_id=pk)
        followings = Follow.objects.filter(follower=user)  # TODO: order?

        serializer = UserFollowingSerializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Social Login : Kakao
# According to notion docs, front will get authorization code from kakao auth server
# so backend has to get token from kakao api server
KAKAO_KEY = get_secret("CLIENT_ID")
REDIRECT_URI = get_secret("REDIRECT_URI")


class KaKaoSignInView(APIView):  # front's job but for test..
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        kakao_auth_url = "https://kauth.kakao.com/oauth/authorize?response_type=code"
        response = redirect(f'{kakao_auth_url}&client_id={KAKAO_KEY}&redirect_uri={REDIRECT_URI}')
        return response


class KakaoCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        # 1. get token
        code = request.GET.get("code")   # TODO tell front (request / query param)
        kakao_token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_KEY,
            'redirect_uri': REDIRECT_URI,
            'code': code,
            # 'client_secret': '', # Not required but.. for security
        }
        response = requests.post(kakao_token_url, data=data).json()
        access_token = response.get("access_token")
        if not access_token:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'failed to get access_token'})

        # 2. get user information
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer ${access_token}"},).json()
        kakao_id = user_info_response.get("id")
        if not kakao_id:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'failed to get kakao_id'})

        # TODO: are you going to get user profile, too???

        # 3. connect kakao account - user
        # user signed up with kakao -> enable kakao login (Q. base login?)
        # case 1. user who has signed up with kakao account trying to login
        kakao_account = SocialAccount.objects.filter(account_id=kakao_id)
        if kakao_account:
            user = kakao_account.first().user
            token = jwt_token_of(user)
            redirect(FRONT_URL)
            response['Authorization'] = "JWT " + token
            url = FRONT_URL + user.user_id
            redirect(url)
            return response
            # return Response({'success': True, 'token': token, 'user_id': user.user_id}, status=status.HTTP_200_OK)

        # case 2. new user signup with kakao (might use profile info)
        else:
            random_id = unique_random_id_generator()
            fake_email = unique_random_email_generator()
            user = User(user_id=random_id, email=fake_email)  # (tmp) user_id, fake email
            user.set_unusable_password()  # user signed up with kakao can only login via kakao login
            user.save()
            kakao_account = SocialAccount.objects.create(account_id=kakao_id, type='kakao', user=user)
            token = jwt_token_of(user)
            url = FRONT_URL + user.user_id
            redirect(url)
            response['Authorization'] = "JWT " + token
            return response
            # return Response({'token': token, 'user_id': user.user_id}, status=status.HTTP_201_CREATED)

class UserRecommendView(APIView):  # recommend random ? users who I don't follow
    queryset = User.objects.all().reverse()
    permission_classes = (permissions.IsAuthenticated,)

    # GET /api/v1/recommend/  TODO: Q. request.user? or specify..?
    def get(self, request):
        me = request.user
        unfollowing_users = self.queryset.exclude(Q(following__follower=me) | Q(pk=me.pk))[:3]

        if unfollowing_users.count() < 3:
            return Response(status=status.HTTP_200_OK, data={'message': "not enough users to recommend"})

        serializer = UserRecommendSerializer(unfollowing_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FollowRecommendView(APIView):  # recommend random ? users who I don't follow
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    # GET /api/v1/follow/{pk}/recommend/  tmp
    def get(self, request, pk=None):
        me = request.user
        try:
            new_following = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such user exists'})

        followings = User.objects.filter(following__follower=new_following)
        recommending_users = followings.exclude(Q(following__follower=me) | Q(pk=me.pk))[:3]

        if recommending_users.count() < 3:
            return Response(status=status.HTTP_200_OK, data={'message': "not enough users to recommend"})

        serializer = UserRecommendSerializer(recommending_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)