from django.db import models
from django.conf import settings
from django.utils.timezone import now


def user_directory_path(instance, filename):
    """Har bir foydalanuvchi uchun maxsus papka yaratish"""
    return f"receipts/{instance.user.id}/{now().strftime('%Y/%m/%d')}/{filename}"


class PaymentRequest(models.Model):
    """💳 Foydalanuvchi to‘lov so‘rovlarini saqlash va tarix sifatida ishlatish"""

    TRANSACTION_TYPES = [
        ("deposit", "Kiritish"),
        ("withdraw", "Chiqim"),
    ]

    PAYMENT_METHODS = [
        ("card", "Karta"),
        ("admin", "Admin orqali"),
    ]

    STATUS_CHOICES = [
        ("pending", "⏳ Kutilmoqda"),
        ("approved", "✅ Tasdiqlandi"),
        ("rejected", "❌ Rad etildi"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 💰 To‘lov summasi
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES,
                                        default="deposit")  # ✅ Pul kirish yoki chiqish
    receipt = models.ImageField(upload_to="receipts/", blank=True, null=True)  # 📸 Chek rasmi
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payments"
    )  # ✅ Admin tomonidan tasdiqlangan
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")  # 📌 Holati
    created_at = models.DateTimeField(auto_now_add=True)  # 📅 Sana va vaqt
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="card")

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.get_status_display()})"
