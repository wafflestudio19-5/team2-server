from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, permissions, viewsets
from rest_framework.views import Response, APIView
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.serializers import UserCreateSerializer, UserInfoSerializer, UserLoginSerializer, FollowSerializer, UserFollowSerializer, UserFollowingSerializer, UserProfileSerializer
from django.db import IntegrityError
from user.models import Follow, User
import requests
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
        return Response(data={'ping': 'pong'}, status=status.HTTP_200_OK)

class EmailSignUpView(APIView):   #signup with email
    permission_classes = (permissions.AllowAny, )

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
            return Response(status=status.HTTP_409_CONFLICT)
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
    permission_classes = (permissions.AllowAny,)  # later change to Isauthenticated

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
            return Response(status=status.HTTP_409_CONFLICT, data='user already follows followee')
        return Response(status=status.HTTP_201_CREATED) #TODO: recommend user

class UserUnfollowView(APIView):
    permission_classes = (permissions.AllowAny,)  # later change to Isauthenticated

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='user_id'),
        }
    ))

    def delete(self, request):
        target_id = request.data.get('user_id', None)
        if target_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='you have specifiy user you want to unfollow')
        try:
            following = User.objects.get(user_id=target_id)
            follow_relation = Follow.objects.get(follower=request.user, following=following)
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='no such user exists')
        except Follow.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='you can unfollow only currently following user')
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
        user = get_object_or_404(User, pk=pk)
        followers = Follow.objects.filter(following=user) # TODO: order?

        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /api/v1/follow_list/{lookup}/following/
    @action(detail=True, methods=['GET'])
    def following(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        followings = Follow.objects.filter(follower=user)  # TODO: order?

        serializer = UserFollowingSerializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserInfoViewSet(viewsets.GenericViewSet):
    serializer_class = UserInfoSerializer
    permission_classes = (permissions.AllowAny,)

    # GET /user/{user_user_id}/
    def retrieve(self, request, pk=None):
        if pk == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, user_id=pk)

        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH /user/id/
    @action(detail=False, methods=['patch'], name='Id')
    def id(self, request):
        user = request.user

        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /user/{user_id}/profile/
    @action(detail=True, methods=['get'], url_path='profile', url_name='profile')
    def profile(self, request, pk=None):
        if pk == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, user_id=pk)

        serializer = UserProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH /user/profile/
    @action(detail=False, methods=['patch'], url_path='profile', url_name='profile')
    def patch_profile(self, request):
        user = request.user

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

# Social Login : Kakao
# According to notion docs, front will get authorization code from kakao auth server
# so backend has to get token from kakao api server

# redirect uri = TODO
class KakaoCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        # 1. get token
        code = request.GET.get("code") # TODO tell front (request / query param)
        kakao_token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            'grant_type': 'authorization_code',
            'client_id': '',
            'redirect_uri': '', #TODO,
            'code': code,
            'client_secret': '', # Not required but.. for security
        }
        response = requests.post(kakao_token_url, data=data).json()
        access_token = response.get("access_token")

        # 2. get user information
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer ${access_token}"},).json()
        kakao_id = user_info_response.get("id")
        # TODO: are you going to get user profile, too???

        # 3. connect kakao account - user
        # case 1. connect existing twitter account - kakao account


        # case 2. new user signup with kakao (might use profile info)