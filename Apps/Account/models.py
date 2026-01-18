from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(unique=True)
    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    profile_image = models.ImageField(
        _("profile image"),
        upload_to="profile_pics/",
        blank=True,
        null=True
    )
    phone_number = models.CharField(_("phone number"), max_length=15, blank=True, null=True)
    bio = models.TextField(_("bio"), max_length=500, blank=True, null=True)
    last_seen = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)

    def get_avatar_initials(self):
        user = self.user
        if user.first_name or user.last_name:
            return f"{user.first_name[:1]}{user.last_name[:1]}".upper()
        return user.username[:2].upper()

    def __str__(self):
        return self.user.username