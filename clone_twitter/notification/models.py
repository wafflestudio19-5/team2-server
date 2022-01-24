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