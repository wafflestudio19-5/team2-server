from django.urls import path, include
from rest_framework.routers import SimpleRouter


from tweet.views import TweetPostView, ReplyView, RetweetView, TweetDetailView, LikeView, HomeView, RetweetCancelView, UnlikeView, ThreadViewSet, QuoteView, TweetSearchViewSet

router = SimpleRouter()


urlpatterns = [
    path('', include(router.urls))
]