from datetime import date
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q, Max
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Chat, Message, MessageRead
from Apps.Account.models import UserProfile

User = get_user_model()

class ChatHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'ChatApp/home.html'

    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.is_online = True
        profile.last_seen = timezone.now()
        profile.save()

        chats = Chat.objects.filter(participants=request.user).annotate(
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time')

        return render(request, self.template_name, {
            'chats': chats,
            'current_user': request.user,
            'today': date.today(),
            'is_home_page': True
        })

class ChatRoomView(LoginRequiredMixin, TemplateView):
    template_name = 'ChatApp/room.html'

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)

        messages_qs = chat.messages.all().order_by('timestamp')

        unread = messages_qs.exclude(sender=request.user).exclude(
            read_by__user=request.user
        )
        for msg in unread:
            MessageRead.objects.get_or_create(message=msg, user=request.user)

        chats = Chat.objects.filter(participants=request.user).annotate(
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time')

        return render(request, self.template_name, {
            'chat': chat,
            'messages': messages_qs,
            'current_user': request.user,
            'chats': chats,
            'active_chat_id': chat_id,
            'today': date.today(),
            'is_home_page': False
        })

class StartChatView(LoginRequiredMixin, View):

    def get(self, request, user_id):
        other_user = get_object_or_404(User, id=user_id)

        if other_user == request.user:
            messages.error(request, "You cannot chat with yourself.")
            return redirect('ChatApp:home')

        with transaction.atomic():
            chat = Chat.objects.filter(
                chat_type='private',
                participants=request.user
            ).filter(
                participants=other_user
            ).annotate(
                pcount=Max('participants')
            ).first()

            if chat:
                return redirect('ChatApp:room', chat_id=chat.id)

            chat = Chat.objects.create(chat_type='private')
            chat.participants.add(request.user, other_user)

        messages.success(
            request,
            f"Started conversation with {other_user.get_full_name() or other_user.username}"
        )
        return redirect('ChatApp:room', chat_id=chat.id)


class ChatMessagesAPIView(LoginRequiredMixin, View):

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        data = []

        for msg in chat.messages.all().order_by('timestamp'):
            data.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%I:%M %p'),
                'is_own': msg.sender == request.user
            })

        return JsonResponse({'messages': data})

class SearchUsersAPIView(LoginRequiredMixin, View):

    def get(self, request):
        query = request.GET.get('q', '')
        if not query:
            return JsonResponse({'users': []})

        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10].select_related('profile')[:10]

        results = []
        for user in users:
            profile = getattr(user, 'profile', None)
            results.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
                'initials': profile.get_avatar_initials() if profile else user.username[:2].upper(),
                'profile_image': profile.profile_image.url if profile and profile.profile_image else None,
                'is_online': profile.is_online if profile else False
            })

        return JsonResponse({'users': results})
