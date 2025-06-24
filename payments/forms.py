from django import forms
from .models import PaymentRequest


class PaymentRequestForm(forms.ModelForm):
    """💳 Foydalanuvchi balansga pul to‘lash uchun forma"""

    class Meta:
        model = PaymentRequest
        fields = ["amount", "receipt"]  # Foydalanuvchi faqat shu maydonlarni to‘ldiradi

    def init(self, *args, **kwargs):
        super().init(*args, **kwargs)
        self.fields["amount"].widget.attrs.update({"class": "form-control", "placeholder": "Miqdorni kiriting"})
        self.fields["card_number"].widget.attrs.update({"class": "form-control", "placeholder": "Karta raqamingiz"})
        self.fields["receipt"].widget.attrs.update({"class": "form-control"})