from django.contrib import admin
from .models import BusinessChat, BusinessChatMessage, ChatMessage, Chat


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_sender', 'user_receiver')

    def user_sender(self, chat):
        return chat.sender.username

    def user_receiver(self, chat):
        return chat.receiver.username


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "content")


@admin.register(BusinessChatMessage)
class BusinessChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "content")


@admin.register(BusinessChat)
class BusinessChatAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "business")
