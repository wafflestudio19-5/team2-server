from rest_framework import serializers

from tweet.models import Tweet


class TweetWriteSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, max_length=500)
    media = serializers.FileField(required=False)

    def create(self, validated_data):
        me = self.context['request'].user

        tweet_type = 1
        author = me
        content = validated_data.get('content')
        media = validated_data.get('media', None)

        tweet = Tweet.objects.create(tweet_type=tweet_type, author=author, content=content, media=media)

        return tweet

