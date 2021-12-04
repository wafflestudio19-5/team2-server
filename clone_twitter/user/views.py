from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.views import Response, APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.serializers import UserCreateSerializer
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

    def post(self, request, *args, **kwargs):

        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, jwt_token = serializer.save()

        return Response({'email': user.email, 'token': jwt_token}, status=status.HTTP_201_CREATED)
