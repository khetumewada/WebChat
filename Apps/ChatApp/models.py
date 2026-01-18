# import uuid
# from django.db import models
# from django.conf import settings
#
# User = settings.AUTH_USER_MODEL
#
#
# class ChatRoom(models.Model):
#     ROOM_TYPES = (
#         ("private", "Private"),
#         ("group", "Group"),
#     )
#     room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     created_by = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="created_rooms"
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         ordering = ["-updated_at"]
#
#     def __str__(self):
#         members = list(self.members.all())
#         if len(members) == 2:
#             return f"{members[0].user} ↔ {members[1].user}"
#         return str(self.id)
#
#     def get_other_user(self, user):
#         member = self.members.exclude(user=user).first()
#         return member.user if member else None
#
#     def get_last_message(self):
#         return self.messages.order_by("-created_at").first()
#
#
# class ChatRoomMember(models.Model):
#     room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="members")
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#
#     class Meta:
#         unique_together = ("room", "user")
#
#     def __str__(self):
#         return f"{self.user} in {self.room}"
#
#
# class Message(models.Model):
#     room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
#     sender = models.ForeignKey(User, on_delete=models.CASCADE)
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         ordering = ["created_at"]

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Chat(models.Model):
    CHAT_TYPES = (
        ('private', 'Private'),
        ('group', 'Group'),
    )

    name = models.CharField(max_length=100, blank=True)
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPES, default='private')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.chat_type == 'private' and self.name == "":
            return f"Private Chat ({self.id})"
        # if self.chat_type == 'private':
            # participants = list(self.participants.all())
            # if len(participants) == 2:
            #     return f"Chat between {participants[0].username} and {participants[1].username}"
        return self.name or f"Chat {self.id}"

    def get_other_participant(self, user):
        """Get the other participant in a private chat"""
        if self.chat_type == 'private':
            return self.participants.exclude(id=user.id).first()
        return None

    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')
