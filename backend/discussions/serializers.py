from rest_framework import serializers

from discussions.models import EventDiscussionMessage
from profiles.serializers import ShortUserProfileSerializer


class DiscussionEventSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.CharField()
    cover = serializers.FileField()

    def get_id(self, event):
        return event.uuid


class EventDiscussionMessageSerializer(serializers.ModelSerializer):
    sender = ShortUserProfileSerializer()

    class Meta:
        model = EventDiscussionMessage
        fields = ("id", "sender", "content", "created_at")


'''
    Don't forget the unread_count
'''


class EventDiscussionSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    event = DiscussionEventSerializer()
    messages = serializers.SerializerMethodField()
    muted = serializers.SerializerMethodField()

    def get_id(self, discussion):
        return f"discussion_{discussion.id}"

    def get_messages(self, discussion):
        messages = EventDiscussionMessage.objects.filter(discussion=discussion)[0:10]
        serialized = EventDiscussionMessageSerializer(messages, many=True)
        return serialized.data

    def get_muted(self, discussion):
        user = self.context.get("user")
        return user in discussion.muted_by.all()
