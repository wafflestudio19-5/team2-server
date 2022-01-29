from django.db import models

from tweet.models import Tweet
from user.models import User


class Mention(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='mentions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentioned_by')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tweet'],
                name='unique mention'
            )
        ]


class Notification(models.Model):
    TYPE = (
        ('LIKE', 'like'),
        ('REPLY', 'reply'),
        ('RETWEET', 'retweet'),
        ('FOLLOW', 'follow'),
        ('MENTION', 'mention'),
    )

    noti_type = models.CharField(choices=TYPE, max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notify')
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='notify_in', null=True)
    notified = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notified')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)