from django.urls import path, include
from rest_framework.routers import SimpleRouter
from user.views import PingPongView, EmailSignUpView, SearchPeopleView, UserInfoViewSet, UserLoginView, \
    UserFollowView, UserUnfollowView, FollowListViewSet, KakaoCallbackView, KaKaoSignInView, \
    UserRecommendView, FollowRecommendView, UserDeactivateView, KakaoDeactivateView

router = SimpleRouter()
router.register('follow_list', FollowListViewSet, basename='follow_list')  # /api/v1/follow_list/
router.register('user', UserInfoViewSet, basename='user') # /api/v1/user/

urlpatterns = [
    path('ping/', PingPongView.as_view(), name='ping'),  # /api/v1/ping/
    path('signup/', EmailSignUpView.as_view(), name='signup'),  # /api/v1/signup/
    path('login/', UserLoginView.as_view(), name='login'),  # /api/v1/login/
    path('deactivate/', UserDeactivateView.as_view(), name='deactivate'),  # /api/v1/deactivate/
    path('follow/', UserFollowView.as_view(), name='follow'),  # /api/v1/follow/  TODO refactor
    path('unfollow/<str:user_id>/', UserUnfollowView.as_view(), name='unfollow'),  # /api/v1/unfollow/{user_id}/
    path('recommend/', UserRecommendView.as_view(), name='recommend'),  # /api/v1/recommend/
    path('follow/<int:pk>/recommend/', FollowRecommendView.as_view(), name='follow-recommend'), #tmp
    path('kakao/signup/', KaKaoSignInView.as_view(), name='kakao-signup'),
    path('kakao/unlink/', KakaoDeactivateView.as_view(), name='kakao-unlink'),
    path('search/people/', SearchPeopleView.as_view(), name='search-people'), # /api/v1/search/people/
    path('', include(router.urls))
]