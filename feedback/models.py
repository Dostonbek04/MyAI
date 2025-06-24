from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

def validate_feedback_length(value):
    if len(value) > 150:
        raise ValidationError("Fikr juda uzun! Iltimos, 500 ta belgidan kamroq bo‘lsin.")

class Feedback(models.Model):
    """📝 Foydalanuvchi fikrlari"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")  # ✅ Foydalanuvchi bilan bog‘lash
    email = models.EmailField()  # ✅ Foydalanuvchi emaili
    message = models.TextField(validators=[validate_feedback_length])
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ Fikr qoldirilgan vaqt

    def __str__(self):
        return f"Fikr: {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"
