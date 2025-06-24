# presentations/forms.py
from django import forms
from .models import Presentation

# Shablon turlari
TEMPLATE_CHOICES = [
    ("light", "Light"),
    ("dark", "Dark"),
    ("professional", "Professional"),
]

class PresentationForm(forms.ModelForm):
    template_type = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        label="Shablon turi",
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Taqdimot uchun shablon turini tanlang: Light, Dark yoki Professional."
    )
    list_count = forms.ChoiceField(
        choices=[
            ("8", "8"),
            ("10", "10"),
            ("15", "15"),
            ("20", "20"),
            ("25", "25"),
            ("30", "30"),
        ],
        label="Listlar soni",
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Bitta slaydda 8 dan 30 gacha list tanlashingiz mumkin."
    )
    style_index = forms.IntegerField(
        min_value=-1,
        max_value=49,
        initial=-1,
        label="Shablon dizayn raqami (-1 = Random)",
        widget=forms.HiddenInput()  # Foydalanuvchi HTML’da radio button orqali tanlaydi
    )
    with_images = forms.BooleanField(
        required=False,
        initial=True,
        label="Rasmlar bilanmi?",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Rasmlar OpenAI DALL·E yordamida generatsiya qilinadi (qo‘shimcha xarajat talab qilishi mumkin)."
    )

    class Meta:
        model = Presentation
        fields = ["title", "template_type", "list_count", "style_index", "with_images"]
        labels = {
            "title": "Taqdimot mavzusi",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Taqdimot mavzusini kiriting"}),
        }

    def clean_list_count(self):
        list_count = int(self.cleaned_data.get("list_count"))
        if list_count not in [8, 10, 15, 20, 25, 30]:
            raise forms.ValidationError("Listlar soni 8, 10, 15, 20, 25 yoki 30 bo‘lishi kerak.")
        return list_count

    def clean_style_index(self):
        style_index = self.cleaned_data.get("style_index")
        if style_index is None:
            raise forms.ValidationError("Shablon dizayn raqamini tanlang.")
        if style_index < -1 or style_index > 49:
            raise forms.ValidationError("Shablon dizayn raqami -1 (random) yoki 0 dan 49 gacha bo‘lishi kerak.")
        return style_index