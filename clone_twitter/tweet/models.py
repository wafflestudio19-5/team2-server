from django.db import models
from user.models import User


class Tweet(models.Model):
    TYPE = (
        ('GENERAL', 'general'),
        ('REPLY', 'reply'),
        ('RETWEET', 'retweet'),
        ('QUOTE', 'quote_retweet'),
    )

    tweet_type = models.CharField(choices=TYPE, max_length=10)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tweets')
    retweeting_user = models.CharField(max_length=20, blank=True)
    reply_to = models.CharField(max_length=20, blank=True)
    # retweeting_user, reply_to : User.user_id
    content = models.CharField(max_length=500)
    media = models.FileField()  # TODO connect to S3. (we store only urls/key in DB)
    created_at = models.DateTimeField(auto_now_add=True)

class Reply(models.Model):
    replied = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='replied_by')
    replying = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='replying_to')

class Retweet(models.Model):
    retweeted = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='retweeted_by')
    retweeting = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='retweeting')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='retweets')

class UserLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    liked = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='liked_by')