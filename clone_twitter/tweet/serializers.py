from rest_framework import serializers

from tweet.models import Tweet, Reply, Retweet


class TweetWriteSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, max_length=500)
    media = serializers.FileField(required=False)

    def validate(self, data):
        content = data.get('content', '')
        media = data.get('media', None)
        if not content and not media:
            raise serializers.ValidationError("neither content nor media")
        return data

    def create(self, validated_data):
        tweet_type = 'GENERAL'
        author = self.context['request'].user
        content = validated_data.get('content', '')
        media = validated_data.get('media', None)

        tweet = Tweet.objects.create(tweet_type=tweet_type, author=author, content=content, media=media)

        return tweet


class ReplySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    content = serializers.CharField(required=False, max_length=500)
    media = serializers.FileField(required=False)

    def validate(self, data):
        content = data.get('content', '')
        media = data.get('media', None)
        if not content and not media:
            raise serializers.ValidationError("neither content nor media")
        return data


    def create(self, validated_data):
        tweet_id = validated_data.get('id')
        try:
            replied = Tweet.objects.get(id=tweet_id)
        except Tweet.DoesNotExist:
            return False

        tweet_type = 'REPLY'
        author = self.context['request'].user
        reply_to = replied.author.user_id
        content = validated_data.get('content', '')
        media = validated_data.get('media', None)

        replying = Tweet.objects.create(tweet_type=tweet_type, author=author, reply_to=reply_to, content=content, media=media)
        reply = Reply.objects.create(replied=replied, replying=replying)

        return True


class RetweetSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        tweet_id = validated_data.get('id')
        try:
            retweeted = Tweet.objects.get(id=tweet_id)
        except Tweet.DoesNotExist:
            return False

        me = self.context['request'].user
        tweet_type = 'RETWEET'
        author = retweeted.author
        retweeting_user = me.user_id
        content = retweeted.content
        media = retweeted.media

        exist = retweeted.retweeted_by.filter(user=me)
        if not exist:
            retweeting = Tweet.objects.create(tweet_type=tweet_type, author=author, retweeting_user=retweeting_user, content=content, media=media)
            retweet = Retweet.objects.create(retweeted=retweeted, retweeting=retweeting, user=me)
        else:
            false = Retweet.objects.create(retweeted=retweeted, retweeting=retweeted, user=me)

        return True
