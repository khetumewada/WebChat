import socket
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import logging

logger = logging.getLogger("Apps.Account.tasks")

EMAIL_RETRY_CONFIG = dict(
    bind=True,
    autoretry_for=(SMTPException, socket.error),
    retry_kwargs={"max_retries": 3, "countdown": 10},
    retry_backoff=True,
    retry_jitter=True,
)

@shared_task(name="account.send_welcome_register_email", **EMAIL_RETRY_CONFIG)
def send_welcome_register_email(self, email):
    logger.info(f"[START] welcome register email -> {email}")

    try:
        subject = "Welcome to EmailNotifier!"
        message = (
            "Hi,\n\n"
            "You have registered successfully! 🎉\n"
            "Thanks for joining us.\n\n"
            "— Team EmailNotifier"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        logger.info(f"[SUCCESS] welcome register email sent -> {email}")

    except Exception as e:
        logger.error(
            f"[FAIL] welcome register email -> {email}",
            exc_info=True
        )
        raise self.retry(exc=e)

@shared_task(name="account.send_welcome_login_email",ignore_result=True, **EMAIL_RETRY_CONFIG)
def send_welcome_login_email(self, email):
    logger.info(f"[START] welcome login email -> {email}")

    try:
        subject = "Welcome-Back to EmailNotifier!"
        message = (
            "Hi,\n\n"
            "You have logged in successfully! 🎉\n"
            "Thanks for joining us.\n\n"
            "— Team EmailNotifier"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        logger.info(f"[SUCCESS] welcome login email sent -> {email}")

    except Exception as e:
        logger.error(
            f"[FAIL] welcome login email -> {email}",
            exc_info=True
        )
        raise self.retry(exc=e)

@shared_task(name="account.send_otp_email", **EMAIL_RETRY_CONFIG)
def send_otp_email(self, email, otp):
    logger.info(f"[START] send_otp_email -> {email}")

    try:
        send_mail(
            subject="Your OTP for Registration",
            message=f"Your OTP code is {otp}. It will expire in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(f"[SUCCESS] OTP sent -> {email}")

    except Exception as e:
        logger.error(
            f"[FAIL] OTP send failed -> {email}",
            exc_info=True
        )
        raise self.retry(exc=e)

User = get_user_model()
@shared_task(name="account.send_password_reset_email", **EMAIL_RETRY_CONFIG)
def send_password_reset_email(self, reset_url, user_id):
    logger.info(f"[START] password reset -> user_id={user_id}")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"[SKIP] user not found -> {user_id}")
        return

    try:
        messages = (
            f"Hello {user.username},\n\n"
            f"Click the link below to reset your password:\n"
            f"{reset_url}\n\n"
            "— Team EmailNotifier"
        )

        send_mail(
            subject = "Password reset mail",
            message=messages,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"[SUCCESS] password reset -> {user.email}")

    except Exception:
        logger.error(
            f"[FAIL] password reset -> {user.email}",
            exc_info=True
        )
        raise self.retry()