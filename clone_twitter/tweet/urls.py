from django.urls import path, include
from rest_framework.routers import SimpleRouter

from tweet.views import TweetPostView

router = SimpleRouter()

urlpatterns = [
    path('tweet/', TweetPostView.as_view(), name='post'),  # /api/v1/tweet/
]