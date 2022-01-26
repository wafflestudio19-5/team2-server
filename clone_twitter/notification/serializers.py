from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import serializers

from notification.models import Mention
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