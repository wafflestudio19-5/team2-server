from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from notification.models import Mention, Notification
User = get_user_model()


def mention(user_id, tweet):
    try:
        user = User.objects.get(user_id=user_id)
        mention = Mention.objects.create(tweet=tweet, user=user)
        return mention
    except User.DoesNotExist:
        return None
    except IntegrityError:
        return None


def notify(me, user_id, tweet, noti_type):
    try:
        notified = User.objects.get(user_id=user_id)
        notification = Notification.objects.create(noti_type=noti_type, user=me, tweet=tweet, notified=notified)
        return notification
    except User.DoesNotExist:
        return None
    except IntegrityError:
        return None


def notify_all(me, tweet, noti_type, replying=None):
    author_id = tweet.author.user_id
    mentioned_list = [x.user.user_id for x in tweet.mentions.all()]
    if replying:
        tweet = replying
    notify(me, author_id, tweet, noti_type)
    for mentioned in mentioned_list:
        notify(me, mentioned, tweet, noti_type)


class NotificationView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def patch(self, request):
        from notification.serializers import NotificationListSerializer
        me = request.user
        serializer = NotificationListSerializer(me, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)