from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    """📝 Fikr yozish formasi"""
    class Meta:
        model = Feedback
        fields = ["message"]  # ✅ Faqatgina fikr yozish maydoni
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Fikringizni shu yerga yozing..."
            })
        }
