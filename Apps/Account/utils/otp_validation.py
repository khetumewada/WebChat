import random

from django.core.cache import caches

otp_cache = caches["otp_cache"]
OTP_EXPIRY = 300  # 5 minutes


def generate_otp(email):
    otp = random.randint(100000, 999999)
    otp_cache.set(f"otp:{email}", otp, timeout=OTP_EXPIRY)
    return otp


def validate_otp(email, user_otp):
    email = email.strip().lower()
    if not user_otp:
        return False, "OTP is required"

    cached = otp_cache.get(f"otp:{email}")
    if not cached:
        return False, "OTP expired or not sent"
    if str(cached) != str(user_otp):
        return False, "Invaild OTP!"
    return True, None


def clear_otp(email):
    email = email.strip().lower()
    otp_cache.delete(f"otp:{email}")
