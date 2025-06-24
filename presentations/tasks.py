import os
import datetime
from django.conf import settings
from .models import Presentation

def delete_old_presentations():
    """📌 24 soatdan oshgan fayllarni serverdan o‘chirish."""
    old_presentations = Presentation.objects.filter(created_at__lt=datetime.datetime.now() - datetime.timedelta(days=1))

    for presentation in old_presentations:
        if presentation.file and os.path.exists(presentation.file.path):
            os.remove(presentation.file.path)  # ✅ Serverdan o‘chirish
            print(f"✅ {presentation.file.name} o‘chirildi.")
