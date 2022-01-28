import json
from multiprocessing.sharedctypes import Value
import re
from django.test import tag

import twitter
import user.paginations
from django.db.models.expressions import Case, When
from django.contrib.auth import authenticate
from twitter.utils import unique_random_id_generator, unique_random_email_generator
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, permissions, viewsets
from rest_framework.views import Response, APIView
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.serializers import UserCreateSerializer, UserInfoSerializer, UserLoginSerializer, FollowSerializer, UserFollowSerializer, UserFollowingSerializer, UserProfileSerializer, UserSearchInfoSerializer, jwt_token_of, UserRecommendSerializer
from django.db import IntegrityError, transaction
from django.db.models import Q, Count
from user.models import Follow, User, SocialAccount, ProfileMedia
import requests
from twitter.settings import get_secret, FRONT_URL
from user.paginations import UserListPagination
from twitter.authentication import CustomJWTAuthentication

# for email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from twitter.utils import account_activation_token, active_message
from django.utils.encoding import force_bytes, force_text
from .tasks import send_email_task

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

class TokenVerifyView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(data={'is_valid_token': True}, status=status.HTTP_200_OK)

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

class UserDeactivateView(APIView): # deactivate
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        me = request.user
        password = request.data.get('password', None)
        if hasattr(me, 'social_account'):
            return Response({'message': "social login user cannot deactivate account via this api"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(user_id=me.user_id, password=password)

        if user is None:
            return Response({'message': "password is wrong"}, status=status.HTTP_401_UNAUTHORIZED)

        retweets = user.retweets.select_related('retweeting').all()
        for retweet in retweets:
            retweet.retweeting.delete()

        user.delete()
        return Response({'success': True}, status=status.HTTP_200_OK)

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

    def delete(self, request, user_id=None):  # unfollow/{target_id}/
        target_id = user_id
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
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = user.paginations.UserListPagination

    # GET /api/v1/follow_list/{lookup}/follower/
    @action(detail=True, methods=['GET'])
    def follower(self, request, pk=None):
        user = get_object_or_404(User, user_id=pk)
        followers = Follow.objects.filter(following=user).order_by('-created_at')
        page = self.paginate_queryset(followers)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(followers, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /api/v1/follow_list/{lookup}/following/
    @action(detail=True, methods=['GET'])
    def following(self, request, pk=None):
        user = get_object_or_404(User, user_id=pk)
        followings = Follow.objects.filter(follower=user).order_by('-created_at')
        page = self.paginate_queryset(followings)

        if page is not None:
            serializer = UserFollowingSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = UserFollowingSerializer(followings, many=True, context={'request': request})
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

        serializer = self.get_serializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH /user/id/
    @action(detail=False, methods=['patch'], name='Id')
    def id(self, request):
        user = request.user

        serializer = self.get_serializer(user, data=request.data, partial=True, context={'request': request})
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

        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH /user/profile/
    @action(detail=False, methods=['patch'], url_path='profile', url_name='profile')
    def patch_profile(self, request):
        user = request.user

        serializer = UserProfileSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

# Social Login : Kakao

KAKAO_KEY = get_secret("CLIENT_ID")
REDIRECT_URI = get_secret("REDIRECT_URI")

# get authorization code from kakao auth server
class KaKaoSignInView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        kakao_auth_url = "https://kauth.kakao.com/oauth/authorize?response_type=code"
        response = redirect(f'{kakao_auth_url}&client_id={KAKAO_KEY}&redirect_uri={REDIRECT_URI}')
        return response

# get access token from kakao api server
class KakaoCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        # 1. get token
        code = request.GET.get("code") # TODO tell front (request / query param)
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
            url = FRONT_URL + "oauth/callback/kakao/?code=null" + "&message=failed to get access_token"
            response = redirect(url)
            return response

        # 2. get user information
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer ${access_token}"},).json()
        kakao_id = user_info_response.get("id")
        if not kakao_id:
            url = FRONT_URL + "oauth/callback/kakao/?code=null" + "&message=failed to get kakao_id"
            response = redirect(url)
            return response

        user_info = user_info_response["kakao_account"]
        profile = user_info["profile"]
        nickname = profile['nickname']
        profile_img_url = profile.get("profile_image_url")
        is_default_image = profile.get("is_default_image", True)
        email = user_info.get("email", None)


        # 3. connect kakao account - user
        # user signed up with kakao -> enable kakao login (Q. base login?)
        # case 1. user who has signed up with kakao account trying to login
        kakao_account = SocialAccount.objects.filter(account_id=kakao_id, type='kakao')
        if kakao_account:
            user = kakao_account.first().user
            token = jwt_token_of(user)
            url = FRONT_URL + "oauth/callback/kakao/?code=" + token + "&user_id=" + user.user_id
            response = redirect(url)

            return response

        # case 2. new user signup with kakao (might use profile info)
        else:
            random_id = unique_random_id_generator(User)

            if email and User.objects.filter(email=email).exists():
                url = FRONT_URL + "oauth/callback/kakao/?code=null" + "&message=duplicate email"
                response = redirect(url)
                return response

            user = User(user_id=random_id, email=email, username=nickname)
            user.set_unusable_password()  # user signed up with kakao can only login via kakao login
            user.save()

            if not is_default_image:
                profile_media = ProfileMedia(image_url=profile_img_url)
            else:
                profile_media = ProfileMedia()
            profile_media.user = user
            profile_media.save()

            kakao_account = SocialAccount.objects.create(account_id=kakao_id, type='kakao', user=user)
            token = jwt_token_of(user)
            url = FRONT_URL + "oauth/callback/kakao/?code=" + token + "&user_id=" + user.user_id
            response = redirect(url)

            return response

ADMIN_KEY = get_secret("ADMIN_KEY")

class KakaoUnlinkView(APIView): # deactivate
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        me = request.user
        if not hasattr(me, 'social_account'):  # TODO add account type checking after google social login
            return Response({'message': "normal user cannot deactivate account via this api"}, status=status.HTTP_400_BAD_REQUEST)

        kakao_id = me.social_account.account_id
        # 2. unlink kakao account
        kakao_unlink_url = "https://kapi.kakao.com/v1/user/unlink"
        data = {
            'target_id_type': 'user_id',
            'target_id': kakao_id,
        }
        auth_header = "KakaoAK " + ADMIN_KEY
        user_unlink_response = requests.post(kakao_unlink_url, data=data, headers={"Authorization": auth_header,
                                             "Content-Type": "application/x-www-form-urlencoded"}).json()
        unlinked_user_id = user_unlink_response.get("id")

        if not unlinked_user_id:
            return Response({'message': "failed to get unlinked user_id"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. delete related social account object
        kakao_account = SocialAccount.objects.get(account_id=kakao_id)
        me = kakao_account.user

        # delete related retweets
        retweets = me.retweets.select_related('retweeting').all()
        for retweet in retweets:
            retweet.retweeting.delete()

        me.delete()
        return Response({'success':True, 'user_id':unlinked_user_id}, status=status.HTTP_200_OK)

# Social Login : Google
GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
GOOGLE_CALLBACK_URI = get_secret("GOOGLE_CALLBACK")
GOOGLE_SECRET = get_secret("GOOGLE_SECRET")

class GoogleSignInView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
        client_id = GOOGLE_CLIENT_ID
        return redirect(
            f"{google_auth_url}?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}")

class GoogleCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        # 1. get token
        client_id = GOOGLE_CLIENT_ID
        client_secret = GOOGLE_SECRET
        code = request.GET.get('code')

        token_res = requests.post(
            f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}"
            + f"&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}").json()  #state?
        error = token_res.get("error")
        if error is not None:
            url = FRONT_URL + "oauth/callback/google/?code=null" + "&message=error"
            response = redirect(url)
            return response

        access_token = token_res.get('access_token')

        # get email, profile
        user_info_response = requests.get(f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={access_token}").json()

        # TODO exception
        google_id = user_info_response.get("sub")
        username = user_info_response.get("given_name")
        email = user_info_response.get("email", None)
        profile_img_url = user_info_response.get("picture")
        if len(profile_img_url) > 200:
            profile_img_url = ProfileMedia.default_profile_img

        # 3. connect google account - user
        # case 1. user who has signed up with google account trying to login
        google_account = SocialAccount.objects.filter(account_id=google_id, type='google')  #TODO add type = google
        if google_account:
            user = google_account.first().user
            token = jwt_token_of(user)
            url = FRONT_URL + "oauth/callback/google/?code=" + token + "&user_id=" + user.user_id
            response = redirect(url)
            return response

        # case 2. new user signup with google (might use profile info)
        else:
            random_id = unique_random_id_generator(User)

            if email and User.objects.filter(email=email).exists():
                url = FRONT_URL + "oauth/callback/google/?code=null" + "&message=duplicate email"
                response = redirect(url)
                return response

            with transaction.atomic():
                user = User(user_id=random_id, email=email, username=username)
                user.set_unusable_password()  # user signed up with google can only login via kakao login
                user.save()
                profile_media = ProfileMedia(image_url=profile_img_url)
                profile_media.user = user
                profile_media.save()

            if user is not None:
                google_account = SocialAccount.objects.create(account_id=google_id, type='google', user=user)
                token = jwt_token_of(user)
                url = FRONT_URL + "oauth/callback/google/?code=" + token + "&user_id=" + user.user_id
                response = redirect(url)
                return response
            return redirect(FRONT_URL + "oauth/callback/google/?code=null" + "&message=creation failed")

class UserRecommendView(APIView):  # recommend random ? users who I don't follow
    queryset = User.objects.all().reverse()
    permission_classes = (permissions.IsAuthenticated,)

    # GET /api/v1/recommend/  TODO: Q. request.user? or specify..?
    def get(self, request):
        me = request.user
        unfollowing_users = self.queryset.exclude(Q(following__follower=me) | Q(pk=me.pk))[:3]

        if unfollowing_users.count() < 3:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': "not enough users to recommend"})

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
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': "not enough users to recommend"})

        serializer = UserRecommendSerializer(recommending_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SearchPeopleView(APIView, UserListPagination):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    # GET /api/v1/search/people/
    # include 
    def get(self, request):
        if not request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'no query provided'})
        search_keywords = request.query_params['query']
        search_keywords = list(filter(lambda x: x != '', re.split(r'%20|\+', search_keywords)))
        tag_keywords = ['']

        for k in range(len(search_keywords)):
            if search_keywords[k][0] == '@':
                search_keywords[k] = search_keywords[k][1:]
                tag_keywords.append(search_keywords[k])


        sorted_queryset = \
            User.objects.all() \
            .annotate(num_keywords_included=sum([Case(When(Q(username__icontains=keyword) | Q(user_id__icontains=keyword) | Q(bio__icontains=keyword), then=1), default=0) for keyword in search_keywords]),
                num_keywords_in_username=sum([Case(When(Q(username__icontains=keyword), then=1), default=0) for keyword in search_keywords]),
                is_tag_keyword=sum([Case(When(user_id=keyword, then=1), default=0) for keyword in tag_keywords]),
                num_followers=Count('following')) \
            .filter(num_keywords_included__gte=1) \
            .order_by('-is_tag_keyword', '-num_keywords_in_username', '-num_keywords_included', '-num_followers')

        page = self.paginate_queryset(sorted_queryset, request)

        if page is not None:
            serializer = UserInfoSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = UserInfoSerializer(sorted_queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


DOMAIN = get_secret("DOMAIN")
class SignupEmailSendView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    # authentication_classes = (CustomJWTAuthentication,)  # unactive user doesn't get error

    def post(self, request):
        # TODO exception when email = null or target_email is someone other's email
        target_email = request.data.get('email', None)
        user = request.user
        domain = "127.0.0.1:8000" if twitter.settings.DEBUG else DOMAIN
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        message_data = active_message(domain, uidb64, token)
        mail_title = "[Team2] waffletwitter 가입을 위한 인증 이메일입니다."
        mail_to = user.email  # default: user's email
        if target_email is not None:
            mail_to = target_email

        send_email_task.delay(mail_title, message_data, mail_to) # celery task
        return Response({"message": "email sent to user"}, status=status.HTTP_200_OK)

class EmailActivateView(APIView):
    permission_classes = (permissions.AllowAny,)
    # authentication_classes = (CustomJWTAuthentication,)  # unactive user doesn't get error

    def get(self, request, uidb64=None, token=None):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if user is not None and account_activation_token.check_token(user, token):
                User.objects.filter(pk=uid).update(is_verified=True)
                return Response({"message": "email verification success"}, status=status.HTTP_200_OK)  # TODO Q front redirect?
            return Response({"message": "AUTH_FAIL"}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError:
            return Response({"message": "KEY_ERROR"}, status=status.HTTP_400_BAD_REQUEST)
