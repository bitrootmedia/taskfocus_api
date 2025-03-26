from rest_framework import serializers

from .models import DirectMessage, DirectMessageAck, DirectThread, Message, Thread


class ThreadSerializer(serializers.ModelSerializer):
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Thread
        fields = ["id", "task_id", "project_id", "unread_count", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class MessageAckSerializer(serializers.Serializer):
    message_ids = serializers.ListField(child=serializers.UUIDField(format="hex_verbose"), allow_empty=False)


class DirectThreadSerializer(serializers.ModelSerializer):
    unseen_messages_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DirectThread
        fields = ["id", "users", "created_at", "updated_at", "unseen_messages_count"]


class DirectMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectMessage
        fields = ["id", "thread", "sender", "content", "created_at", "updated_at"]


class DirectMessageAckSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectMessageAck
        fields = ["id", "message", "user", "seen_at"]
