from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers

from notification.models import Mention, Notification
from tweet.models import Tweet
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
