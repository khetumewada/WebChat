from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email", widget=forms.EmailInput())

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        full_name = self.cleaned_data["username"].strip()
        parts = full_name.split()

        if len(parts) >= 2:
            user.first_name = parts[0]
            user.last_name = " ".join(parts[1:])
        else:
            user.first_name = full_name
            user.last_name = ""

        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    image = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'image']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Your phone number'}),
        }