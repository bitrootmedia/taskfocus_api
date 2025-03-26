from rest_framework import serializers

from core.models import User

from .models import DirectMessage, DirectMessageAck, DirectThread, Message, Thread


class ThreadSerializer(serializers.ModelSerializer):
    unread_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Thread
        fields = ["id", "task_id", "project_id", "unread_count", "created_at", "user"]
        extra_kwargs = {"user": {"write_only": True}}


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class MessageAckSerializer(serializers.Serializer):
    message_ids = serializers.ListField(child=serializers.UUIDField(format="hex_verbose"), allow_empty=False)


class DirectThreadSerializer(serializers.ModelSerializer):
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DirectThread
        fields = ["id", "users", "created_at", "updated_at", "unread_count"]

    def validate_users(self, users):
        """
        Ensure that the users list has at least 2 valid users.
        """
        if len(users) < 2:
            raise serializers.ValidationError("A direct thread must have at least 2 users.")

        user_ids = [user.id for user in users]
        existing_users = User.objects.filter(id__in=user_ids).count()

        if existing_users != len(users):
            raise serializers.ValidationError("One or more users do not exist.")

        return users


class DirectMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectMessage
        fields = ["id", "thread", "sender", "content", "created_at", "updated_at"]


class DirectMessageAckSerializer(serializers.Serializer):
    message_ids = serializers.ListField(child=serializers.UUIDField(format="hex_verbose"), allow_empty=False)
