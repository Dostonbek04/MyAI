
import comtypes.client
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files import File
import io
from PIL import Image
import os
from django.conf import settings
import comtypes.client
from django.utils import timezone
import uuid
from .managers import CustomUserManager
import random
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    # ... (boshqa kodlar o‘zgarmaydi)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_premium = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    # Ikkala kodda bir xil bo‘lgan qismlar birlashtirildi
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="user",
    )

    def __str__(self):
        return self.username

class EmailVerification(models.Model):
    """Model to store email verification codes"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True, default="000000")
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(auto_now_add=True)  # Yangi qo‘shilgan maydon
    expires_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.code or self.code == "000000":
            self.code = str(random.randint(100000, 999999))
        if not self.expires_at or self.expires_at == timezone.now():
            self.expires_at = timezone.now() + timedelta(minutes=15)
        if not self.pk:  # Faqat yangi obyektda last_sent_at ni o‘rnatsin
            self.last_sent_at = timezone.now()
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def can_resend(self):
        """Qayta yuborishga ruxsat berishni tekshiradi (2 daqiqa kutish kerak)"""
        return (timezone.now() - self.last_sent_at).total_seconds() >= 120  # 2 daqiqa

    def __str__(self):
        return f"{self.user.email} - {self.code}"

class SiteStatistics(models.Model):
    """Model to store site statistics"""
    total_users = models.PositiveIntegerField(default=0)
    new_users_today = models.PositiveIntegerField(default=0)
    total_presentations = models.PositiveIntegerField(default=0)
    new_presentations_today = models.PositiveIntegerField(default=0)
    total_paid_users = models.PositiveIntegerField(default=0)
    last_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Site statistics"

class Profile(models.Model):
    """Model to store user profile information"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='profile_images/', default='default/default_profile.png')
    email_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} profile"

class Notification(models.Model):
    """Model to store user notifications"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

class Presentation(models.Model):
    """Model to store presentation data"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_presentations')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_presentations')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='presentations/', blank=True, null=True)
    preview_image = models.ImageField(upload_to='previews/', blank=True, null=True)
    template_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dropbox_url = models.URLField(max_length=500, null=True, blank=True)

    def delete_old_preview_image(self):
        """Delete old preview image if it exists"""
        if self.preview_image and os.path.exists(self.preview_image.path):
            os.remove(self.preview_image.path)
            self.preview_image.delete(save=False)

    def generate_preview_image(self):
        """Generate preview image from the first slide of the .pptx file using comtypes"""
        if not self.file or not os.path.exists(self.file.path):
            return None

        try:
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = 1
            presentation = powerpoint.Presentations.Open(self.file.path)
            if presentation.Slides.Count > 0:
                first_slide = presentation.Slides[1]
                temp_image_path = os.path.join(settings.MEDIA_ROOT, 'temp', f"{self.id}_temp_preview.png")
                os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)
                first_slide.Export(temp_image_path, "PNG", 800, 600)
                with Image.open(temp_image_path) as img:
                    temp_buffer = io.BytesIO()
                    img.save(temp_buffer, format="PNG")
                    temp_buffer.seek(0)
                presentation.Close()
                powerpoint.Quit()
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                return temp_buffer
            else:
                presentation.Close()
                powerpoint.Quit()
                return None
        except Exception as e:
            print(f"Error generating preview image with comtypes: {e}")
            try:
                presentation.Close()
                powerpoint.Quit()
            except:
                pass
            return None

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Presentation.objects.get(pk=self.pk)
                if old_instance.preview_image and old_instance.preview_image != self.preview_image:
                    old_instance.delete_old_preview_image()
            except Presentation.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if not self.preview_image and self.file:
            try:
                image_buffer = self.generate_preview_image()
                if image_buffer:
                    preview_filename = f"{self.id}_preview.png"
                    self.preview_image.save(preview_filename, File(image_buffer), save=False)
                    super().save(*args, **kwargs)
                else:
                    self.preview_image = 'default/default_presentation_preview.png'
                    super().save(*args, **kwargs)
            except Exception as e:
                print(f"Error saving preview image: {e}")
                self.preview_image = 'default/default_presentation_preview.png'
                super().save(*args, **kwargs)

# Signal to create a Profile when a CustomUser is created
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Signal to save the Profile whenever the CustomUser is saved
@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()