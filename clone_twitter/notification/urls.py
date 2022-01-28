from django.urls import path, include
from rest_framework.routers import SimpleRouter

from notification.views import NotificationView, NotificationCountView

router = SimpleRouter()


urlpatterns = [
    path('notification/', NotificationView.as_view(), name='notification'),                                # /api/v1/notification/
    path('notification/count/', NotificationCountView.as_view(), name='notification_count'),                    # /api/v1/notification/count/
    path('', include(router.urls))
]