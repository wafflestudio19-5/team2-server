from django.urls import path, include
from rest_framework.routers import SimpleRouter

from tweet.views import TweetPostView, ReplyView, RetweetView

router = SimpleRouter()

urlpatterns = [
    path('tweet/', TweetPostView.as_view(), name='post'),             # /api/v1/tweet/
    path('reply/', ReplyView.as_view(), name='reply'),                # /api/v1/reply/
    path('retweet/', RetweetView.as_view(), name='retweet'),          # /api/v1/retweet/
]