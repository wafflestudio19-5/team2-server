from django.urls import path, include
from rest_framework.routers import SimpleRouter

from tweet.views import HomeView, TweetPostView, ReplyView, RetweetView, TweetDetailView, LikeView, TweetSearchViewSet

router = SimpleRouter()
router.register('search', TweetSearchViewSet, basename='search')  # /api/v1/search/

urlpatterns = [
    path('tweet/', TweetPostView.as_view(), name='post'),             # /api/v1/tweet/
    path('tweet/<int:pk>/', TweetDetailView.as_view(), name='post'),  # /api/v1/tweet/{tweet_id}/
    path('reply/', ReplyView.as_view(), name='reply'),                # /api/v1/reply/
    path('retweet/', RetweetView.as_view(), name='retweet'),          # /api/v1/retweet/
    path('like/', LikeView.as_view(), name='like'),                   # /api/v1/like/
    path('home/', HomeView.as_view(), name='home'),                   # /api/v1/home/                 # /api/v1/retweet/
    path('', include(router.urls))
]