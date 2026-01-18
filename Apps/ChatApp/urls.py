from django.urls import path
from .views import (
    ChatHomeView,
    ChatRoomView,
    StartChatView,
    ChatMessagesAPIView,
    SearchUsersAPIView
)

app_name = 'ChatApp'

urlpatterns = [
    path('home/', ChatHomeView.as_view(), name='home'),
    path('chat/<int:chat_id>/', ChatRoomView.as_view(), name='room'),
    path('start-chat/<int:user_id>/', StartChatView.as_view(), name='start_chat'),
    path('api/chat/<int:chat_id>/messages/', ChatMessagesAPIView.as_view(), name='get_chat_messages'),
    path('api/search-users/', SearchUsersAPIView.as_view(), name='search_users'),
]
