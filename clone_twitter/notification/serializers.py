from rest_framework import serializers

from notification.models import Notification
from tweet.serializers import UserSerializer, custom_paginator, TweetSummarySerializer


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ['created_at', 'is_read', 'notified']

    user = UserSerializer(read_only=True)
    tweet = TweetSummarySerializer(read_only=True)
    written_by_me = serializers.SerializerMethodField()

    def get_written_by_me(self, notification):
        tweet = notification.tweet
        if tweet is None:
            return False
        author = tweet.author
        me = self.context['request'].user

        return author == me


class NotificationListSerializer(serializers.Serializer):
    notifications = serializers.SerializerMethodField()

    def get_notifications(self, me):
        request = self.context['request']
        if self.context['mention']:
            notifications = me.notified.select_related('tweet').filter(noti_type='MENTION').order_by('-created_at')
        else:
            notifications = me.notified.select_related('tweet').all().order_by('-created_at')
        notification, previous_page, next_page = custom_paginator(notifications, 10, request)
        serializer = NotificationSerializer(notification, context={'request': request}, many=True)
        data = serializer.data
        # print(data)

        pagination_info = dict()
        pagination_info['previous'] = previous_page
        pagination_info['next'] = next_page

        data.append(pagination_info)
        return data

    def update(self, me, validated_data):
        notifications = me.notified.all()
        for notification in notifications:
            notification.is_read = True
            notification.save()
        return me