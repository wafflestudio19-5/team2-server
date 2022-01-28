from django.urls import path, include
from rest_framework.routers import SimpleRouter


from tweet.views import TweetPostView, ReplyView, RetweetView, TweetDetailView, LikeView, HomeView, RetweetCancelView, UnlikeView, ThreadViewSet, QuoteView, TweetSearchViewSet, UserTweetsViewSet

router = SimpleRouter()
router.register('tweet', ThreadViewSet, basename='thread')                          # /api/v1/tweet/
router.register('search', TweetSearchViewSet, basename='search')  # /api/v1/search/
router.register('usertweets', UserTweetsViewSet, basename='usertweets') # /api/v1/usertweets/

urlpatterns = [
    path('tweet/', TweetPostView.as_view(), name='post'),                           # /api/v1/tweet/
    path('tweet/<int:pk>/', TweetDetailView.as_view(), name='thread_and_delete'),   # /api/v1/tweet/{tweet_id}/
    path('reply/', ReplyView.as_view(), name='reply'),                              # /api/v1/reply/
    path('retweet/', RetweetView.as_view(), name='retweet'),                        # /api/v1/retweet/
    path('retweet/<int:pk>/', RetweetCancelView.as_view(), name='undo_retweet'),    # /api/v1/retweet/{src_tweet_id}/
    path('quote/', QuoteView.as_view(), name='quote'),                              # /api/v1/retweet/
    path('like/', LikeView.as_view(), name='like'),                                 # /api/v1/like/
    path('like/<int:pk>/', UnlikeView.as_view(), name='unlike'),                    # /api/v1/like/
    path('home/', HomeView.as_view(), name='home'),                                 # /api/v1/home/
    path('', include(router.urls))
]