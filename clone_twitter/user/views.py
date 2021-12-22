from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.views import Response, APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.serializers import UserCreateSerializer, UserLoginSerializer
from django.db import IntegrityError
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

        # try:
        user, jwt_token = serializer.save()
        # except IntegrityError:
        #    return Response(status=status.HTTP_409_CONFLICT)
        return Response({'token': jwt_token}, status=status.HTTP_201_CREATED)

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

        return Response({'success': True, 'token': token}, status=status.HTTP_200_OK)

# TODO: Logout.. expire token and add blacklist.. ?