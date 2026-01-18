from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile
from django.contrib.auth import authenticate
import re



class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    otp = forms.CharField(max_length=6, required=False)

    # validate_username
    def clean_username(self):
        username = self.cleaned_data["username"]

        if " " in username:
            raise ValidationError("Username must not contain spaces. Use '_' instead.")

        if not re.match(r"^[A-Za-z0-9_]+$", username):
            raise ValidationError("Username can contain only letters, numbers and underscore.")

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username is already taken.")

        return username

    # validate_email
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email=email).exists():
            raise ValidationError("Email is already registered.")

        return email

    # validate()
    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match")

            validate_password(password)

        return cleaned_data

    # create()
    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]

        parts = username.split("_")
        first_name = parts[0].capitalize() if len(parts) > 0 else ""
        last_name = parts[1].capitalize() if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        return user


class LoginForm(forms.Form):
    username_or_email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get("username_or_email")
        password = cleaned_data.get("password")

        if not username_or_email or not password:
            raise ValidationError("Both fields are required")

        if "@" in username_or_email:
            user = User.objects.filter(email=username_or_email.lower()).first()
            if not user:
                raise ValidationError("Invalid username/email or password")
            username = user.username
        else:
            username = username_or_email

        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError("Invalid username/email or password")

        cleaned_data["user"] = user
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'profile_image', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
        }
