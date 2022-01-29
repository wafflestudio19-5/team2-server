from urllib.parse import unquote, unquote_plus
import re
from user.models import User
import tweet.paginations
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

from tweet.serializers import TweetSearchInfoSerializer, TweetWriteSerializer, ReplySerializer, RetweetSerializer, \
    TweetDetailSerializer, \
    LikeSerializer, HomeSerializer, UserListSerializer, custom_paginator, TweetSerializer, QuoteSerializer, \
    SearchSerializer
from datetime import datetime, timedelta
from user.permissions import IsVerified


class TweetPostView(APIView):      # write tweet
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'content': openapi.Schema(type=openapi.TYPE_STRING, description='content'),
            'media': openapi.Schema(type=openapi.TYPE_FILE, description='media'),
        }
    )
    responses = {
        201: 'Successfully write tweet',
        400: 'Invalid input data: Neither content nor media',
        401: 'Unauthorized user',
        405: 'Method not allowed: only POST',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Tweet"], request_body=request_body, responses=responses)

    def post(self, request):
        serializer = TweetWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully write tweet'})


class TweetDetailView(APIView):     # open thread of the tweet
    permission_classes = (permissions.AllowAny, )

    responses = {
        200: TweetDetailSerializer,
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: GET or DELETE',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Thread"], responses=responses)

    def get(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        if tweet.tweet_type == 'RETWEET':
            tweet = tweet.retweeting.all()[0].retweeted

        serializer = TweetDetailSerializer(tweet, context={'request': request})
        return Response(serializer.data)

    responses = {
        200: 'Successfully delete tweet',
        401: 'Unauthorized user',
        403: "Forbidden: cannot delete others' tweet",
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: GET or DELETE',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Tweet"], responses=responses)

    def delete(self, request, pk):
        me = request.user
        if me.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'message': 'login first'})
        tweet = get_object_or_404(Tweet, pk=pk)
        if (tweet.tweet_type != 'RETWEET' and tweet.author != me) or (tweet.tweet_type == 'RETWEET' and tweet.retweeting_user != me.user_id):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'message': 'you can delete only your tweets'})

        retweetings = tweet.retweeted_by.all()
        for retweeting in retweetings:
            retweeting.retweeting.delete()

        tweet.delete()
        return Response(status=status.HTTP_200_OK, data={'message': 'successfully delete tweet'})

class ReplyView(APIView):       # reply tweet
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
            'content': openapi.Schema(type=openapi.TYPE_STRING, description='content'),
            'media': openapi.Schema(type=openapi.TYPE_FILE, description='media'),
        }
    )
    responses = {
        201: 'Successfully reply tweet',
        400: 'Invalid input data: Neither content nor media',
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only POST',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Reply"], request_body=request_body, responses=responses)

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


class RetweetView(APIView):       # do retweet
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
        }
    )
    responses = {
        201: 'Successfully do retweet tweet',
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only POST',
        409: 'Conflict: already retweeted this tweet',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Retweet"], request_body=request_body, responses=responses)

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


class RetweetCancelView(APIView):     # cancel retweet
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    responses = {
        200: 'Successfully cancel retweet',
        401: 'Unauthorized user',
        403: "Forbidden: you have not retweeted this tweet",
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only DELETE',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Retweet"], responses=responses)

    def delete(self, request, pk):
        me = request.user
        source_tweet = get_object_or_404(Tweet, pk=pk)

        if source_tweet.tweet_type == 'RETWEET':
            source_tweet = source_tweet.retweeting.all()[0].retweeted

        try:
            retweeting = source_tweet.retweeted_by.get(user=me).retweeting
        except Retweet.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have not retweeted this tweet'})
        retweeting.delete()
        return Response(status=status.HTTP_200_OK, data={'message': 'successfully cancel retweet'})


class QuoteView(APIView):            # quote-retweet
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
            'content': openapi.Schema(type=openapi.TYPE_STRING, description='content'),
            'media': openapi.Schema(type=openapi.TYPE_FILE, description='media'),
        }
    )
    responses = {
        201: 'Successfully quote and retweet',
        400: 'Invalid input data: Neither content nor media',
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only POST',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Quote"], request_body=request_body, responses=responses)

    def post(self, request):
        serializer = QuoteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            success = serializer.save()
            if not success:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully quote and retweet'})


class LikeView(APIView):       # do like
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    request_body = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='tweet_id'),
        }
    )
    responses = {
        201: 'Successfully like tweet',
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only POST',
        409: 'Conflict: already liked this tweet',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Like"], request_body=request_body, responses=responses)

    def post(self, request):
        serializer = LikeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            success = serializer.save()
            if not success:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'no such tweet exists'})
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT, data={'message': 'you already liked this tweet'})
        return Response(status=status.HTTP_201_CREATED, data={'message': 'successfully like tweet'})


class UnlikeView(APIView):      # cancel like
    permission_classes = (permissions.IsAuthenticated, IsVerified)

    responses = {
        200: 'Successfully unlike tweet',
        401: 'Unauthorized user',
        403: "Forbidden: you have not liked this tweet",
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only DELETE',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Like"], responses=responses)

    def delete(self, request, pk):
        me = request.user
        tweet = get_object_or_404(Tweet, pk=pk)

        try:
            user_like = tweet.liked_by.get(user=me)
        except UserLike.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'you have not liked this tweet'})
        user_like.delete()
        return Response(status=status.HTTP_200_OK, data={'message': 'successfully cancel like'})


class HomeView(APIView):        # home
    permission_classes = (permissions.IsAuthenticated, )

    responses = {
        200: HomeSerializer,
        401: 'Unauthorized user',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Home"], responses=responses)

    def get(self, request):
        me = request.user
        serializer = HomeSerializer(me, context={'request': request})
        return Response(serializer.data)


class TweetSearchViewSet(viewsets.GenericViewSet):
    serializer_class = TweetSearchInfoSerializer
    permission_classes = (permissions.IsAuthenticated,)

    pagination_class = tweet.paginations.TweetListPagination

    responses = {
        200: TweetSearchInfoSerializer,
        400: 'Invalid input data: no query provided',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Search"], query_serializer=SearchSerializer, responses=responses)

    # GET /search/top/
    @action(detail=False, methods=['get'], url_path='top', url_name='top')
    def get_top(self, request):
        if not request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'no query provided'})
        search_keywords = unquote_plus(request.query_params['query']).split()
        sorted_queryset = \
            Tweet.objects.all() \
            .annotate(num_keywords_included=sum([Case(When(Q(author__username__icontains=keyword) | Q(author__user_id__icontains=keyword) | Q(content__icontains=keyword), then=1), default=0) for keyword in search_keywords]),\
                num_replies=Count('replied_by'), num_retweets=Count('retweeted_by'), num_likes=Count('liked_by')) \
            .filter(tweet_type='GENERAL', num_keywords_included__gte=1, written_at__gte=datetime.now()-timedelta(weeks=1)) \
            .order_by('-num_keywords_included', '-num_retweets', '-num_likes', '-num_replies')
        
        page = self.paginate_queryset(sorted_queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(sorted_queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


    responses = {
        200: TweetSearchInfoSerializer,
        400: 'Invalid input data: no query provided',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Search"], query_serializer=SearchSerializer, responses=responses)

    # GET /search/latest/
    @action(detail=False, methods=['get'], url_path='latest', url_name='latest')
    def get_latest(self, request):
        if not request.query_params:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': 'no query provided'})
        search_keywords = unquote_plus(request.query_params['query']).split()
        sorted_queryset = \
            Tweet.objects.all() \
            .annotate(num_keywords_included=sum([Case(When(Q(author__username__icontains=keyword) | Q(author__user_id__icontains=keyword) | Q(content__icontains=keyword), then=1), default=0) for keyword in search_keywords])) \
            .filter(Q(tweet_type='GENERAL') | Q(tweet_type='REPLY'), num_keywords_included__gte=1) \
            .order_by('-num_keywords_included', '-written_at')

        page = self.paginate_queryset(sorted_queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(sorted_queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ThreadViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TweetDetailSerializer
    queryset = Tweet.objects.all()

    success_response = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'retweeting_users': openapi.Schema(type=openapi.TYPE_OBJECT, description='retweeting users'),
        }
    )
    responses = {
        200: success_response,
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Thread"], responses=responses)

    # GET /api/v1/tweet/{lookup}/retweets/
    @action(detail=True, methods=['GET'])
    def retweets(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        if tweet.tweet_type == 'RETWEET':
            tweet = tweet.retweeting.all()[0].retweeted

        retweets = tweet.retweeted_by.all()
        retweeting_user_list = [x.user for x in retweets]
        retweeting_users, previous_page, next_page = custom_paginator(retweeting_user_list, 20, request)
        serializer = UserListSerializer(retweeting_users, many=True, context={'request': request})
        data = serializer.data

        pagination_info = dict()
        pagination_info['previous'] = previous_page
        pagination_info['next'] = next_page

        data.append(pagination_info)
        return Response(data, status=status.HTTP_200_OK)

    responses = {
        200: TweetSerializer,
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Thread"], responses=responses)

    # GET /api/v1/tweet/{lookup}/quotes/
    @action(detail=True, methods=['GET'])
    def quotes(self, request, pk=None):
        tweet = get_object_or_404(Tweet, pk=pk)

        if tweet.tweet_type == 'RETWEET':
            tweet = tweet.retweeting.all()[0].retweeted

        quotes = tweet.quoted_by.select_related('quoting').all().order_by('-quoting__created_at')
        tweet_list = [x.quoting for x in quotes]
        tweets, previous_page, next_page = custom_paginator(tweet_list, 10, request)
        serializer = TweetSerializer(tweets, many=True, context={'request': request})
        data = serializer.data

        pagination_info = dict()
        pagination_info['previous'] = previous_page

        pagination_info['next'] = next_page

        data.append(pagination_info)
        return Response(data=data, status=status.HTTP_200_OK)

    success_response = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'liking_users': openapi.Schema(type=openapi.TYPE_OBJECT, description='liking users'),
        }
    )
    responses = {
        200: success_response,
        401: 'Unauthorized user',
        404: 'Not found: no such tweet exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Thread"], responses=responses)

    # GET /api/v1/tweet/{lookup}/likes/
    @action(detail=True, methods=['GET'])
    def likes(self, request, pk):
        tweet = get_object_or_404(Tweet, pk=pk)

        if tweet.tweet_type == 'RETWEET':
            tweet = tweet.retweeting.all()[0].retweeted

        userlikes = tweet.liked_by.all()
        liking_user_list = [x.user for x in userlikes]
        liking_users, previous_page, next_page = custom_paginator(liking_user_list, 20, request)
        serializer = UserListSerializer(liking_users, many=True, context={'request': request})
        data = serializer.data

        pagination_info = dict()
        pagination_info['previous'] = previous_page
        pagination_info['next'] = next_page

        data.append(pagination_info)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserTweetsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TweetSerializer
    queryset = Tweet.objects.all()
    pagination_class = tweet.paginations.TweetListPagination

    responses = {
        200: TweetSerializer,
        401: 'Unauthorized user',
        404: 'Not found: no such user exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Profile"], responses=responses)

    # GET /api/v1/usertweets/{user_id}/tweets/
    @action(detail=True, methods=['GET'])
    def tweets(self, request, pk=None):
        if pk == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, user_id=pk)

        q = Q()
        q |= (Q(author=user) & Q(tweet_type='GENERAL'))                     # tweets written(or quoted) by the user
        q |= (Q(retweeting_user=user.user_id) & Q(tweet_type='RETWEET'))    # tweets retweeted by the user

        queryset = Tweet.objects.filter(q).order_by('-created_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    responses = {
        200: TweetSerializer,
        401: 'Unauthorized user',
        404: 'Not found: no such user exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Profile"], responses=responses)

    # GET /api/v1/usertweets/{user_id}/tweets_replies/
    @action(detail=True, methods=['GET'])
    def tweets_replies(self, request, pk=None):
        if pk == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, user_id=pk)

        q = Q()
        q |= (Q(author=user) & ~Q(tweet_type='RETWEET'))                    # tweets written(or replied, quoted) by the user
        q |= (Q(retweeting_user=user.user_id) & Q(tweet_type='RETWEET'))    # tweets retweeted by the user
        
        queryset = Tweet.objects.filter(q).order_by('-created_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    responses = {
        200: TweetSerializer,
        401: 'Unauthorized user',
        404: 'Not found: no such user exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Profile"], responses=responses)

    # GET /api/v1/usertweets/{user_id}/media/
    @action(detail=True, methods=['GET'])
    def media(self, request, pk=None):
        if pk == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, user_id=pk)

        q = (Q(author=user) & ~Q(tweet_type='RETWEET'))                    # tweets written(or quoted) by the user

        queryset = Tweet.objects.annotate(media_count=Count('media')).filter(q & Q(media_count__gt=0)).order_by('-created_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    responses = {
        200: TweetSerializer,
        401: 'Unauthorized user',
        404: 'Not found: no such user exists',
        405: 'Method not allowed: only GET',
        500: 'Internal server error'
    }

    @swagger_auto_schema(tags=["Profile"], responses=responses)

    # GET /api/v1/usertweets/{user_id}/likes/
    @action(detail=True, methods=['GET'])
    def likes(self, request, pk=None):
        if pk == 'me':
            user = request.user
        else:
            user = get_object_or_404(User, user_id=pk)

        queryset = Tweet.objects.filter(liked_by__user__user_id__contains=user.user_id).order_by('-liked_by__created_at')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        