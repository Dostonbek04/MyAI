from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from django import forms
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "balance", "is_premium")

class ProfileForm(forms.ModelForm):
    """Foydalanuvchi profili uchun forma"""

    class Meta:
        model = CustomUser
        fields = ["username", "email", "balance", "is_premium"]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]  # Foydalanuvchi rasmni qo‘shish


class CustomUserCreationForm(UserCreationForm):
    """Ro‘yxatdan o‘tish formasi, foydalanuvchi nomi va emailni tekshiradi"""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        """Google orqali ro‘yxatdan o‘tgan email takrorlanmasligi uchun tekshirish"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "❌ Ushbu email allaqachon ro‘yxatdan o‘tgan. Iltimos, boshqa email kiriting yoki tizimga kiring.")
        return email
