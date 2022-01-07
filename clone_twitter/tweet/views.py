from django.db import IntegrityError
from django.db.models.aggregates import Count
from django.db.models.expressions import Case, When
from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from tweet.models import Tweet, Retweet, UserLike
from tweet.serializers import TweetSearchInfoSerializer, TweetWriteSerializer, ReplySerializer, RetweetSerializer, TweetDetailSerializer, \
    LikeSerializer, HomeSerializer
from datetime import datetime, timedelta


class TweetPostView(APIView):      # write & delete tweet
    permission_classes = (permissions.IsAuthenticated, )

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'content': openapi.Schema(type=openapi.TYPE_STRING, description='content'),
            'media': openapi.Schema(type=openapi.TYPE_FILE, description='media'),
        }
    ))

    def post(self, request):
        serializer = TweetWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully write tweet'})

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
        }
    ))

    def delete(self, request):
        me = request.user
        tweet_id = request.data.get('id', None)
        if tweet_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have specify tweet you want to delete'})
        try:
            tweet = Tweet.objects.get(id=tweet_id)
        except Tweet.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})
        if (tweet.tweet_type != 'RETWEET' and tweet.author != me) or (tweet.tweet_type == 'RETWEET' and tweet.retweeting_user != me.user_id):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'message': 'you can delete only your tweets'})

        retweetings = tweet.retweeted_by.all()
        for retweeting in retweetings:
            retweeting.retweeting.delete()

        tweet.delete()
        return Response(status=status.HTTP_200_OK, data={'message': 'successfully delete tweet'})


class TweetDetailView(APIView):     # open thread of the tweet
    permission_classes = (permissions.AllowAny, )

    def get(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)
        if tweet.tweet_type == 'RETWEET':
            tweet = tweet.retweeting.all()[0].retweeted
        serializer = TweetDetailSerializer(tweet, context={'request': request})
        return Response(serializer.data)


class ReplyView(APIView):       # reply tweet
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
            'content': openapi.Schema(type=openapi.TYPE_STRING, description='content'),
            'media': openapi.Schema(type=openapi.TYPE_FILE, description='media'),
        }
    ))

    def post(self, request):
        serializer = ReplySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            success = serializer.save()
            if not success:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully reply tweet'})


class RetweetView(APIView):       # do/cancel retweet
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
        }
    ))

    def post(self, request):
        serializer = RetweetSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            success = serializer.save()
            if not success:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT, data={'message': 'you already retweeted this tweet'})
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully do retweet'})

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'source_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='source_tweet_id'),
        }
    ))

    def delete(self, request):
        me = request.user
        source_tweet_id = request.data.get('source_id', None)
        if source_tweet_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have specify source tweet you want to cancel retweet'})
        try:
            source_tweet = Tweet.objects.get(id=source_tweet_id)
        except Tweet.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such source tweet exists'})

        try:
            retweeting = source_tweet.retweeted_by.get(user=me).retweeting
        except Retweet.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have not retweeted this tweet'})
        retweeting.delete()
        return Response(status=status.HTTP_200_OK, data={'message': 'successfully cancel retweet'})


class LikeView(APIView):       # do/cancel like
    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
        }
    ))

    def post(self, request):
        serializer = LikeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            success = serializer.save()
            if not success:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT, data={'message': 'you already liked this tweet'})
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully like'})

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
        }
    ))

    def delete(self, request):
        me = request.user
        tweet_id = request.data.get('id', None)
        if tweet_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have specify tweet you want to like'})
        try:
            tweet = Tweet.objects.get(id=tweet_id)
        except Tweet.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})

        try:
            user_like = tweet.liked_by.get(user=me)
        except UserLike.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have not liked this tweet'})
        user_like.delete()
        return Response(status=status.HTTP_200_OK, data={'message': 'successfully cancel like'})


class HomeView(APIView):     # home
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        me = request.user
        serializer = HomeSerializer(me, context={'request': request})
        return Response(serializer.data)
class TweetSearchViewSet(viewsets.GenericViewSet):
    serializer_class = TweetSearchInfoSerializer
    permission_classes = (permissions.AllowAny,)
    # GET /search/top/
    @action(detail=False, methods=['get'], url_path='top', url_name='top')
    def get_top(self, request):
        if not request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'no query provided'})
        search_keywords = request.query_params['query'].split()

        sorted_queryset = \
            Tweet.objects.all() \
            .annotate(num_keywords_included=sum([Case(When(Q(author__username__icontains=keyword) | Q(author__user_id__icontains=keyword) | Q(content__icontains=keyword), then=1), default=0) for keyword in search_keywords]),\
                num_replies=Count('replied_by'), num_retweets=Count('retweeted_by'), num_likes=Count('liked_by')) \
            .filter(tweet_type='GENERAL', num_keywords_included__gte=1, written_at__gte=datetime.now()-timedelta(weeks=1)) \
            .order_by('-num_keywords_included', '-num_retweets', '-num_likes', '-num_replies')

        serializer = TweetSearchInfoSerializer(sorted_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /search/latest/
    @action(detail=False, methods=['get'], url_path='latest', url_name='latest')
    def get_latest(self, request):
        if not request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'no query provided'})
        search_keywords = request.query_params['query'].split()

        sorted_queryset = \
            Tweet.objects.all() \
            .annotate(num_keywords_included=sum([Case(When(Q(author__username__icontains=keyword) | Q(author__user_id__icontains=keyword) | Q(content__icontains=keyword), then=1), default=0) for keyword in search_keywords])) \
            .filter(Q(tweet_type='GENERAL') | Q(tweet_type='REPLY'), num_keywords_included__gte=1) \
            .order_by('-num_keywords_included', '-written_at')

        serializer = TweetSearchInfoSerializer(sorted_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
