from django.urls import path

from user.views import PingPongView, EmailSignUpView, UserLoginView, UserFollowView

urlpatterns = [
    path('ping/', PingPongView.as_view(), name='ping'),  # /api/v1/ping/
    path('signup/', EmailSignUpView.as_view(), name='signup'),  # /api/v1/signup/
    path('login/', UserLoginView.as_view(), name='login'),  # /api/v1/login/
    path('follow/', UserFollowView.as_view(), name='follow')  # /api/v1/follow/
]