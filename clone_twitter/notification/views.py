from django.contrib.auth import get_user_model
from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from notification.models import Mention, Notification
from notification.serializers import NotificationListSerializer

User = get_user_model()


class NotificationView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    responses = {
        200: NotificationListSerializer,
        401: 'Unauthorized user',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Notification"], responses=responses)

    def get(self, request):
        me = request.user
        serializer = NotificationListSerializer(me, data=request.data, context={'request': request, 'mention': False})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationMentionView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    responses = {
        200: NotificationListSerializer,
        401: 'Unauthorized user',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Notification"], responses=responses)

    def get(self, request):
        me = request.user
        serializer = NotificationListSerializer(me, data=request.data, context={'request': request, 'mention': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationCountView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    success_response = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'notification_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='notification count'),
        }
    )

    responses = {
        200: success_response,
        401: 'Unauthorized user',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Notification"], responses=responses)

    def get(self, request):
        me = request.user
        notification_count = me.notified.filter(is_read=False).count()
        data = {'notification_count': notification_count}

        return Response(data=data, status=status.HTTP_200_OK)