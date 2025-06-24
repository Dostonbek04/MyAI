import os
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import JSONField  # Yangi JSONField

User = get_user_model()

class Presentation(models.Model):
    """Foydalanuvchi taqdimotlarini saqlash modeli."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="presentations"
    )
    title = models.CharField(max_length=255, default="Untitled Presentation")
    slides_data = JSONField(default=list)  # Slaydlar ma'lumotlari JSON sifatida
    file = models.FileField(upload_to="presentations/", blank=True, null=True)  # Eski umumiy PPTX fayli uchun
    pptx_file = models.FileField(upload_to="presentations/pptx/", blank=True, null=True)  # Yangi PPTX fayli
    pdf_file = models.FileField(upload_to="presentations/pdf/", blank=True, null=True)  # Yangi PDF fayli
    preview_image = models.ImageField(upload_to="presentations/previews/", blank=True, null=True)  # Preview tasviri
    dropbox_url = models.URLField(max_length=500, null=True, blank=True)
    template_type = models.CharField(
        max_length=20,
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
            ("professional", "Professional"),
        ],
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def delete_old_file(self):
        """Serverdagi eski taqdimot faylini va preview rasmni o‘chirish."""
        # Hozirgi file maydoni
        if self.file and os.path.exists(self.file.path):
            os.remove(self.file.path)
        # Yangi pptx_file va pdf_file maydonlari
        if self.pptx_file and os.path.exists(self.pptx_file.path):
            os.remove(self.pptx_file.path)
        if self.pdf_file and os.path.exists(self.pdf_file.path):
            os.remove(self.pdf_file.path)
        # Preview rasmni o‘chirish
        if self.preview_image and os.path.exists(self.preview_image.path):
            os.remove(self.preview_image.path)

    def delete(self, *args, **kwargs):
        """Taqdimot o‘chirilganda barcha bog‘liq fayllar va rasmlarni avtomatik o‘chirish."""
        # Taqdimotga tegishli rasmlarni o‘chirish
        for image in self.images.all():
            image.delete()  # PresentationImage modelining delete metodi chaqiriladi
        # Taqdimot fayli va preview rasmni o‘chirish
        self.delete_old_file()
        # Taqdimotni o‘chirish
        super().delete(*args, **kwargs)

class PresentationImage(models.Model):
    """Har bir slayd uchun rasmni saqlash modeli."""
    presentation = models.ForeignKey(
        Presentation,
        on_delete=models.CASCADE,
        related_name='images'
    )
    slide_number = models.IntegerField(default=1)
    image = models.ImageField(upload_to='presentation_images/')

    def __str__(self):
        return f"Image for {self.presentation.title} - Slide {self.slide_number}"

    def delete_old_image(self):
        """Eski rasmni o‘chirish uchun funksiya."""
        if self.image and os.path.exists(self.image.path):
            os.remove(self.image.path)

    def delete(self, *args, **kwargs):
        """Rasm o‘chirilganda faylni avtomatik o‘chirish."""
        self.delete_old_image()
        super().delete(*args, **kwargs)

class Slide(models.Model):
    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE, related_name='slides')
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} (Slayd {self.order})"