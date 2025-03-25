from rest_framework import serializers
from .models import Thread, Message


class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"


class MessageAckSerializer(serializers.Serializer):
    message_ids = serializers.ListField(child=serializers.UUIDField(format="hex_verbose"), allow_empty=False)
