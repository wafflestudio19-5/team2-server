from django.urls import path, include
from rest_framework.routers import SimpleRouter

from notification.views import NotificationView

router = SimpleRouter()


urlpatterns = [
    path('notification/', NotificationView.as_view(), name='notification'),                    # /api/v1/notification/
    path('', include(router.urls))
]