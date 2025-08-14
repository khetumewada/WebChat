import random

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from WebChat import settings
from .forms import UserProfileForm, CustomRegisterForm
from .models import UserProfile


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return HttpResponse('<div class="error-message">Email is required.</div>')

        otp = generate_otp()
        request.session['otp_register'] = otp
        request.session['email_to_verify_register'] = email

        send_mail(
            subject="Your WebChat OTP Code",
            message=f"Your OTP code is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return HttpResponse('<div class="success-message">OTP sent! Check your email.</div>')
    return HttpResponse(status=400)


@csrf_exempt
@require_POST
def verify_otp_view(request):
    entered_otp = request.POST.get("otp")
    session_otp = request.session.get("otp_register")
    if not session_otp:
        return HttpResponse('<div class="error-message">No OTP was sent.</div>')
    if entered_otp == session_otp:
        return HttpResponse('<div class="success-message" style="margin-top:6px;">✅ Email is verified</div>')
    return HttpResponse('<div class="error-message">Invalid OTP</div>')


def register_view(request):
    is_htmx = request.headers.get("HX-Request") == "true"
    no_layout = is_htmx  # convenient: pass to template

    email_verified = False
    otp_error = None

    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp_register")
        session_email = request.session.get("email_to_verify_register")

        # otp_error = None
        if not session_otp or not entered_otp or entered_otp != session_otp:
            otp_error = 'Invalid or missing OTP.'
        else:
            email_verified = True

        if form.is_valid() and not otp_error:
            user = form.save(commit=False)

            # Check if user came from Google/social
            if request.POST.get('is_google_signup'):

                # Generate username from first_name + last_name
                first_name = form.cleaned_data.get('first_name', '').strip().lower()
                last_name = form.cleaned_data.get('last_name', '').strip().lower()
                base_username = (first_name + last_name).replace(" ", "") or "user"

                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
            else:
                # Normal form signup: use the username entered by the user
                username = form.cleaned_data.get('username').strip()
                if User.objects.filter(username=username).exists():
                    form.add_error('username', 'This username is already taken.')
                    return render(request, 'account/register.html', {'form': form, 'otp_error': otp_error})

            user.username = username
            user.set_password(form.cleaned_data['password1'])
            user.save()

            # Create profile
            UserProfile.objects.create(user=user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Clean session OTP
            request.session.pop('otp_register', None)
            request.session.pop('email_to_verify_register', None)

            if is_htmx:
                response = HttpResponse()
                response["HX-Redirect"] = "/"
                return response
            else:
                return redirect('chatapp:home')

        return render(request, 'account/register.html',
                      {'form': form, 'otp_error': otp_error, 'no_layout': no_layout, 'email_verified': email_verified,
                       })
    else:
        form = CustomRegisterForm()
        return render(request, 'account/register.html',
                      {'form': form, 'no_layout': no_layout, 'email_verified': email_verified,
                       })


@login_required
def logout_view(request):
    """
    Log user out and update online status.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save()

    except UserProfile.DoesNotExist:
        pass

    logout(request)
    messages.success(request, 'You have been log-in successfully.')
    return redirect('account:welcome')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        form.fields['first_name'].initial = user.first_name
        form.fields['last_name'].initial = user.last_name

        if form.is_valid():
            new_email = form.cleaned_data.get('email', '').strip()
            orig_email = user.email

            if new_email != orig_email:
                user.email = new_email

            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.save()
            form.save()

            if request.POST.get("clear_image") == "1":
                if profile.image:
                    profile.image.delete(save=False)
                profile.image = ""
                profile.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('account:profile')
    else:
        form = UserProfileForm(instance=profile)
        form.fields['first_name'].initial = user.first_name
        form.fields['last_name'].initial = user.last_name

    form.fields['email'].initial = user.email

    return render(request, 'account/profile.html', {
        'form': form,
        'profile': profile,
    })


def welcome_view(request):
    """Show welcome page to unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('chatapp:home')
    return render(request, 'account/welcome.html')


def password_reset(request):
    context = {}

    # Step 1: Handle email POST
    if request.method == "POST" and "step" not in request.POST:
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(
                f"?uid={uid}&token={token}&step=reset"
            )
            send_mail(
                subject="Your password reset link",
                message=f"Click the link to reset your password: {reset_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
            context["status"] = "sent"
            context["email"] = email
        except User.DoesNotExist:
            context["status"] = "no_user"
            context["email"] = email

    # Step 2: Handle reset password POST
    elif request.method == "POST" and request.POST.get("step") == "reset":
        uid = request.POST.get("uid")
        token = request.POST.get("token")
        password1 = request.POST.get("new_password1")
        password2 = request.POST.get("new_password2")
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
            if default_token_generator.check_token(user, token):
                if password1 == password2 and len(password1) >= 6:
                    user.set_password(password1)
                    user.save()
                    context["status"] = "done"
                else:
                    context["status"] = "pw_mismatch"
                context["uid"] = uid
                context["token"] = token
            else:
                context["status"] = "invalid"
        except Exception:
            context["status"] = "invalid"

    # Step 3: incoming GET from email link
    elif request.GET.get("step") == "reset" and request.GET.get("uid") and request.GET.get("token"):
        context["show_reset_form"] = True
        context["uid"] = request.GET.get("uid")
        context["token"] = request.GET.get("token")

    return render(request, "account/password_reset.html", context)
