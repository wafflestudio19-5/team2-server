from django.urls import path, include
from rest_framework.routers import SimpleRouter
from user.views import PingPongView, EmailSignUpView, UserLoginView, UserFollowView, UserUnfollowView, FollowListViewSet, KakaoCallbackView, KaKaoSignInView

router = SimpleRouter()
router.register('follow_list', FollowListViewSet, basename='follow_list')  # /api/v1/follow_list/

urlpatterns = [
    path('ping/', PingPongView.as_view(), name='ping'),  # /api/v1/ping/
    path('signup/', EmailSignUpView.as_view(), name='signup'),  # /api/v1/signup/
    path('login/', UserLoginView.as_view(), name='login'),  # /api/v1/login/
    path('follow/', UserFollowView.as_view(), name='follow'),  # /api/v1/follow/  TODO refactor
    path('unfollow/', UserUnfollowView.as_view(), name='unfollow'),  # /api/v1/unfollow/
    path('kakao/signup/', KaKaoSignInView.as_view(), name='kakao-signup'),
    path('', include(router.urls))
]