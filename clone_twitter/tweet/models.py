import os

from django.db import models
from django.utils import timezone
from twitter.utils import media_directory_path

from user.models import User

class Tweet(models.Model):
    TYPE = (
        ('GENERAL', 'general'),
        ('REPLY', 'reply'),
        ('RETWEET', 'retweet'),
    )

    tweet_type = models.CharField(choices=TYPE, max_length=10)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tweets')
    retweeting_user = models.CharField(max_length=20, blank=True)
    reply_to = models.CharField(max_length=20, blank=True)
    # retweeting_user, reply_to : User.user_id
    content = models.CharField(max_length=500, blank=True)
    written_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)


class TweetMedia(models.Model):
    media = models.FileField(upload_to=media_directory_path)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='media')


class Reply(models.Model):
    replied = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True, related_name='replied_by')
    replying = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='replying_to')


class Retweet(models.Model):
    retweeted = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='retweeted_by')
    retweeting = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='retweeting')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='retweets')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'retweeted'],
                name='unique retweet'
            )
        ]


class Quote(models.Model):
    quoted = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='quoted_by')
    quoting = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='quoting')


class UserLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    liked = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='liked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'liked'],
                name='unique like'
            )
        ]