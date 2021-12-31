from django.urls import path, include
from rest_framework.routers import SimpleRouter

from tweet.views import TweetPostView, ReplyView

router = SimpleRouter()

urlpatterns = [
    path('tweet/', TweetPostView.as_view(), name='post'),       # /api/v1/tweet/
    path('reply/', ReplyView.as_view(), name='reply'),          # /api/v1/reply/
]