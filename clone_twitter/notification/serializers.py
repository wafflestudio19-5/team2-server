from django.contrib.auth import get_user_model
from rest_framework import serializers

from notification.models import Mention
from tweet.models import Tweet
User = get_user_model()


def mention(data):

    user_id = data.get('user_id', '')
    tweet_id = data.get('tweet_id', '')
    user = User.objects.get(user_id=user_id)
    tweet = Tweet.objects.get(id=tweet_id)

    mention = Mention.objects.create(tweet=tweet, user=user)
    return mention