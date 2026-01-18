from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.generic import TemplateView
from rest_framework_simplejwt.tokens import RefreshToken
from .forms import RegisterForm, LoginForm, UserProfileForm
from .models import User, UserProfile
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .utils.otp_validation import generate_otp, validate_otp, clear_otp
from .utils.errors import flash_form_errors
from .tasks import send_welcome_register_email, send_password_reset_email, send_otp_email, send_welcome_login_email
import logging

logger = logging.getLogger("Apps.Account.views")


class WelcomeView(TemplateView):
    template_name = "Account/welcome.html"

class SendOTPView(View):
    def post(self, request):
        email = request.POST.get("email")

        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        otp = generate_otp(email.lower())

        try:
            # send_otp_email.delay(email, otp)
            send_mail(
                subject="Your OTP for Registration",
                message=f"Your OTP code is {otp}. It will expire in 5 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

        except Exception as e:
            logger.error(f"Email fail to send otp: {email}")
            return JsonResponse({"message": "Email failed to send!"})

        return JsonResponse({"message": "OTP sent"})

class AsyncPasswordResetView(PasswordResetView):
    template_name = "Account/password_reset/password_reset_form.html"
    # success_url = reverse_lazy("Account:password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse("Account:password_reset_confirm", args=[uid, token])
            )
            print("uid: ",uid)
            print("token:  ",token)
            print("reset: ",reset_url)

            try:
                send_password_reset_email.delay(reset_url, user.id)
            except:
                print("run logger")
                logger.error(f"Reset link fail to send(skip): {user.email}")
                message = (
                    f"Hello {user.username},\n\n"
                    f"Click the link below to reset your password:\n"
                    f"{reset_url}\n\n"
                    "— Team EmailNotifier"
                )
                send_mail(
                    subject="Password reset mail",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

            # success flash message
            messages.success(self.request,"Password reset link has been sent to your email address.",
            )

            return redirect("Account:password_reset_done")

        # user nahi mila → form error + flash message
        form.add_error("email", "No account found with this email address.")
        flash_form_errors(form, self.request)
        return self.form_invalid(form)

class RegisterView(View):
    template_name = "Account/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("ChatApp:home")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)

        if not form.is_valid():
            flash_form_errors(form, request)
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"]
        otp = request.POST.get("otp")

        valid, error = validate_otp(email, otp)
        if not valid:
            messages.error(request, error)
            return render(request, self.template_name, {"form": form})

        form.save()

        clear_otp(email)
        try:
            send_welcome_register_email.delay(email)
        except Exception:
            logger.warning(f"Celery down, skipping welcome register email -> {email}")

        messages.success(request, "Account created successfully")
        return redirect("Account:login")

class LoginView(View):
    template_name = "Account/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("ChatApp:home")
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            flash_form_errors(form, request)
            return render(request, self.template_name, {"form": form})

        user = form.cleaned_data.get("user")

        token = RefreshToken.for_user(user)

        response = redirect("ChatApp:home")
        response.set_cookie("access", str(token.access_token), httponly=True, samesite="Lax")
        response.set_cookie("refresh", str(token), httponly=True, samesite="Lax")

        try:
            send_welcome_login_email.delay(user.email)
        except Exception:
            logger.warning(f"Celery down, skipping login email -> {user.email}")

        return response

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    def post(self, request):
        try:
            refresh = request.COOKIES.get("refresh")
            RefreshToken(refresh).blacklist()
        except:
            pass
        response = redirect("Account:login")
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response

class ProfileView(View):
    template_name = "Account/profile.html"

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("Account:login")

        profile, created = UserProfile.objects.get_or_create(
            user=request.user
        )
        form = UserProfileForm(instance=profile)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("Account:login")

        profile, created = UserProfile.objects.get_or_create(
            user=request.user
        )
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if not form.is_valid():
            flash_form_errors(form, request)
            return render(request, self.template_name, {"form": form})

        user = request.user
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.save()

        profile = form.save(commit=False)

        # CLEAR IMAGE
        if request.POST.get("clear_image") == "1":
            if profile.profile_image:
                profile.profile_image.delete(save=False)
            profile.profile_image = None

        profile.save()
        messages.success(request, "Profile updated successfully")
        return redirect("Account:profile")
