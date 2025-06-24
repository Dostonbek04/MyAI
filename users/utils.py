# users/utils.py
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from django.utils import timezone
from .models import EmailVerification

def send_verification_email(user):
    try:
        if not user.email:
            return False, "Foydalanuvchi emaili topilmadi."
        verification, created = EmailVerification.objects.get_or_create(user=user)
        verification.code = ''.join(random.choices(string.digits, k=6))
        verification.last_sent_at = timezone.now()  # Qayta yuborish vaqtini yangilash
        verification.save()

        subject = "Email Tasdiqlash Kodi"
        message = f"Sizning tasdiqlash kodingiz: {verification.code}\nKod 15 daqiqa davomida amal qiladi."
        print(f"Olindi: {verification.code}")
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True, "Kod yuborildi"
    except Exception as e:
        return False, f"Email yuborishda xatolik: {str(e)}"