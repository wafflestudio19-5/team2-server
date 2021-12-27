from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from tweet.models import Tweet
from tweet.serializers import TweetWriteSerializer


class TweetPostView(APIView):      # write & delete tweet
    permission_classes = (permissions.AllowAny, )

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'content': openapi.Schema(type=openapi.TYPE_STRING, description='content'),
            'media': openapi.Schema(type=openapi.TYPE_FILE, description='media'),
        }
    ))

    def post(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN, data='please login first')

        serializer = TweetWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_201_CREATED, data='successfully write tweet')

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='id'),
        }
    ))

    def delete(self, request):
        me = request.user
        if me.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN, data='please login first')
        tweet_id = request.data.get('id', None)
        if tweet_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='you have specifiy tweet you want to delete')
        try:
            tweet = Tweet.objects.get(id=tweet_id)
        except Tweet.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='no such tweet exists')
        if (tweet.tweet_type != 3 and tweet.author != me) or (tweet.tweet_type == 3 and tweet.retweeting_user != me.user_id):
            return Response(status=status.HTTP_403_FORBIDDEN, data='you can delete only your tweets')
        tweet.delete()
        return Response(status=status.HTTP_200_OK, data='successfully delete tweet')


# class TweetDetailView(APIView):     # delete tweet & open thread of the tweet
#     permission_classes = (permissions.AllowAny, )

