from django.urls import path, include
from rest_framework.routers import SimpleRouter
<<<<<<< Updated upstream
from user.views import PingPongView, EmailSignUpView, UserLoginView, \
    UserFollowView, UserUnfollowView, FollowListViewSet, KakaoCallbackView, KaKaoSignInView, \
    UserRecommendView, FollowRecommendView
=======
from user.views import PingPongView, EmailSignUpView, UserInfoViewSet, UserLoginView, UserFollowView, UserUnfollowView, FollowListViewSet
>>>>>>> Stashed changes

router = SimpleRouter()
router.register('follow_list', FollowListViewSet, basename='follow_list')  # /api/v1/follow_list/
router.register('user', UserInfoViewSet, basename='user') # /api/v1/user/

urlpatterns = [
    path('ping/', PingPongView.as_view(), name='ping'),  # /api/v1/ping/
    path('signup/', EmailSignUpView.as_view(), name='signup'),  # /api/v1/signup/
    path('login/', UserLoginView.as_view(), name='login'),  # /api/v1/login/
    path('follow/', UserFollowView.as_view(), name='follow'),  # /api/v1/follow/  TODO refactor
    path('unfollow/', UserUnfollowView.as_view(), name='unfollow'),  # /api/v1/unfollow/
    path('recommend/', UserRecommendView.as_view(), name='recommend'),  # /api/v1/recommend/
    path('follow/<int:pk>/recommend/', FollowRecommendView.as_view(), name='follow-recommend'), #tmp
    path('kakao/signup/', KaKaoSignInView.as_view(), name='kakao-signup'),
    path('', include(router.urls))
]