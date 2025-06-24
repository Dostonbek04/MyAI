"""
URL configuration for presentlyai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from .views import index  # ✅ index import qilinadi
from users.views import privacy_policy, terms_of_service  # privacy_policy va terms_of_service import qilinadi

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('', index, name='index'),  # ✅ Asosiy sahifa (faqat bitta marta yozildi!)
    path('users/', include('users.urls')),  # users ilovasi uchun URL-lar
    path('presentations/', include('presentations.urls')),  # presentations ilovasi
    path('payments/', include('payments.urls')),  # payments ilovasi
    path('feedback/', include('feedback.urls', namespace="feedback")),  # ✅ feedback ilovasi (faqat bitta marta)
    path("privacy-policy/", privacy_policy, name="privacy_policy"),  # TemplateView o‘rniga privacy_policy ishlatiladi
    path("terms/", terms_of_service, name="terms"),  # TemplateView o‘rniga terms_of_service ishlatiladi
    path("logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),  # ✅ Logout sahifasi
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)