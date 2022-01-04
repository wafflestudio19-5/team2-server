from django.urls import path, include
from rest_framework.routers import SimpleRouter

<<<<<<< HEAD
from tweet.views import TweetPostView, ReplyView, RetweetView, TweetDetailView, LikeView
=======
from tweet.views import TweetPostView, ReplyView, RetweetView, TweetDetailView
>>>>>>> 44f40378eb1d7f9c41f4ef7bde7f0ae477fe48a7

router = SimpleRouter()

urlpatterns = [
    path('tweet/', TweetPostView.as_view(), name='post'),             # /api/v1/tweet/
    path('tweet/<int:pk>/', TweetDetailView.as_view(), name='post'),  # /api/v1/tweet/{tweet_id}/
    path('reply/', ReplyView.as_view(), name='reply'),                # /api/v1/reply/
    path('retweet/', RetweetView.as_view(), name='retweet'),          # /api/v1/retweet/
<<<<<<< HEAD
    path('like/', LikeView.as_view(), name='like'),                   # /api/v1/retweet/
=======
>>>>>>> 44f40378eb1d7f9c41f4ef7bde7f0ae477fe48a7
]