from rest_framework import serializers
from yaml import serialize_all

from core.models import Project, Task, User

from .models import DirectMessage, DirectThread, Message, Thread


class MessengerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "image"]


class MessengerProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title"]
        read_only_fields = ["id", "title"]


class MessengerTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "title"]
        read_only_fields = ["id", "title"]


class ThreadSerializer(serializers.ModelSerializer):
    unread_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Thread
        fields = ["id", "task", "project", "unread_count", "created_at", "user"]
        extra_kwargs = {"user": {"write_only": True}}


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class ThreadAckSerializer(serializers.Serializer):
    seen_at = serializers.DateTimeField()


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


class DirectThreadAckSerializer(serializers.Serializer):
    seen_at = serializers.DateTimeField()


class UserThreadsSerializer(serializers.Serializer):
    user = MessengerUserSerializer()
    unread_count = serializers.IntegerField()
    last_unread_message_date = serializers.DateTimeField()


class UnreadThreadSerializer(serializers.Serializer):
    project = MessengerProjectSerializer()
    task = MessengerTaskSerializer(allow_null=True)
    thread = serializers.UUIDField()
    type = serializers.ChoiceField(choices=["project", "task"])
    name = serializers.CharField()
    last_unread_message_date = serializers.DateTimeField()
    unread_count = serializers.IntegerField()
