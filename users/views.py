# users/views.py
from .models import SiteStatistics, EmailVerification, Profile, Notification, Presentation
from django.utils.timezone import now
from .forms import ProfileUpdateForm, CustomUserCreationForm
from django.contrib.auth import update_session_auth_hash, authenticate, login, get_backends, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from .utils import send_verification_email
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from payments.models import PaymentRequest
from presentations.models import Presentation
from presentations.utils import generate_slide_preview, upload_to_dropbox, delete_from_dropbox
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect

CustomUser = get_user_model()

EMAIL_VERIFICATION_REQUIRED = False

def ensure_preview_images(presentations):
    for presentation in presentations:
        if not presentation.preview_image and presentation.file:
            preview_path = os.path.join(settings.MEDIA_ROOT, "previews", f"{presentation.id}_preview.jpg")
            if generate_slide_preview(presentation.file.path, preview_path):
                presentation.preview_image = f"previews/{presentation.id}_preview.jpg"
                presentation.save()

def index(request):
    base_template = 'authenticated_base.html' if request.user.is_authenticated else 'base.html'
    context = {'base_template': base_template}
    if request.user.is_authenticated:
        return redirect('users:profile')
    return render(request, 'index.html', context)

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if EMAIL_VERIFICATION_REQUIRED:
                user.is_active = False
                user.is_email_verified = False
                user.save()
                EmailVerification.objects.create(user=user)
                send_verification_email(user)
                messages.success(request, "✅ Ro‘yxatdan o‘tish muvaffaqiyatli! Emailingizga 6 xonali kod yuborildi.")
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return JsonResponse({"success": True, "message": "Ro‘yxatdan o‘tish muvaffaqiyatli!"})
            else:
                user.is_active = True
                user.is_email_verified = True
                user.save()
                messages.success(request, "✅ Ro‘yxatdan o‘tish muvaffaqiyatli! Iltimos, tizimga kiring.")
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return JsonResponse({"success": True, "message": "Ro‘yxatdan o‘tish muvaffaqiyatli!"})
        else:
            errors = form.errors.as_json()
            return JsonResponse(
                {"success": False, "message": "Ro‘yxatdan o‘tishda xatolik yuz berdi.", "errors": errors}, status=400)
    return JsonResponse({"success": False, "message": "GET so‘rovlari qabul qilinmaydi."}, status=405)

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=user)

            if EMAIL_VERIFICATION_REQUIRED and not user.is_email_verified:
                messages.error(request, "❌ Emailingiz tasdiqlanmagan. Iltimos, emailingizga yuborilgan kodni kiriting.")
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return JsonResponse(
                    {"success": False, "message": "Email tasdiqlanmagan.", "reason": "email_not_verified"}, status=403)
            login(request, user)
            return JsonResponse({"success": True, "message": "Muvaffaqiyatli kirish!"})
        else:
            return JsonResponse({"success": False, "message": "Noto‘g‘ri foydalanuvchi nomi yoki parol.",
                                 "reason": "invalid_credentials"}, status=401)
    base_template = 'authenticated_base.html' if request.user.is_authenticated else 'base.html'
    return render(request, 'users/login.html', {'base_template': base_template})

@login_required
def verify_code(request):
    if request.method == "POST":
        code = request.POST.get("code")
        print(f"Olindi: {code}")  # Debug uchun
        try:
            verification = EmailVerification.objects.get(user=request.user)
            if verification.is_expired():
                messages.error(request, "❌ Kodning muddati o‘tgan. Iltimos, yangi kod so‘rang.")
                verification.delete()
                return JsonResponse({"success": False, "message": "Kodning muddati o‘tgan.", "reason": "code_expired"},
                                    status=400)
            if verification.code == code:
                user = request.user
                user.is_email_verified = True
                user.is_active = True
                user.save()
                notification = Notification.objects.create(
                    user=user,
                    message="Email muvaffaqiyatli tasdiqlandi!"
                )
                verification.delete()
                messages.success(request, "✅ Email muvaffaqiyatli tasdiqlandi!")
                return JsonResponse({"success": True, "message": "Email muvaffaqiyatli tasdiqlandi!"})
            else:
                messages.error(request, "❌ Noto‘g‘ri kod. Iltimos, qayta urinib ko‘ring.")
                return JsonResponse({"success": False, "message": "Noto‘g‘ri kod.", "reason": "invalid_code"},
                                    status=400)
        except EmailVerification.DoesNotExist:
            messages.error(request, "❌ Tasdiqlash kodi topilmadi. Iltimos, yangi kod so‘rang.")
            return JsonResponse({"success": False, "message": "Tasdiqlash kodi topilmadi.", "reason": "code_not_found"},
                                status=404)
    return JsonResponse({"success": False, "message": "GET so‘rovlari qabul qilinmaydi."}, status=405)

def update_statistics():
    total_users = CustomUser.objects.count()
    new_users_today = CustomUser.objects.filter(date_joined__date=now().date()).count()
    total_presentations = Presentation.objects.count()
    new_presentations_today = Presentation.objects.filter(created_at__date=now().date()).count()
    total_paid_users = PaymentRequest.objects.filter(status="approved").values("user").distinct().count()
    last_payment = PaymentRequest.objects.filter(status="approved").order_by("-created_at").first()
    stats, created = SiteStatistics.objects.get_or_create(id=1)
    stats.total_users = total_users
    stats.new_users_today = new_users_today
    stats.total_presentations = total_presentations
    stats.new_presentations_today = new_presentations_today
    stats.total_paid_users = total_paid_users
    stats.last_payment_amount = last_payment.amount if last_payment else 0
    stats.save()

@require_GET
def total_users(request):
    update_statistics()
    stats = SiteStatistics.objects.first()
    return JsonResponse({
        "total_users": stats.total_users if stats else 0
    })

def site_statistics_view(request):
    update_statistics()
    stats = SiteStatistics.objects.first()
    if not stats:
        return JsonResponse({
            "total_users": 0,
            "new_users_today": 0,
            "total_presentations": 0,
            "new_presentations_today": 0,
            "total_paid_users": 0,
            "last_payment_amount": 0.0,
        })
    return JsonResponse({
        "total_users": stats.total_users,
        "new_users_today": stats.new_users_today,
        "total_presentations": stats.total_presentations,
        "new_presentations_today": stats.new_presentations_today,
        "total_paid_users": stats.total_paid_users,
        "last_payment_amount": float(stats.last_payment_amount),
    })

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Profil muvaffaqiyatli yangilandi!"})
        else:
            errors = form.errors.as_json()
            return JsonResponse({"success": False, "message": "Forma noto‘g‘ri to‘ldirildi.", "errors": errors},
                                status=400)
    return JsonResponse({"success": False, "message": "GET so‘rovlari qabul qilinmaydi."}, status=405)

@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "🔒 Parolingiz muvaffaqiyatli o‘zgartirildi!")
            return JsonResponse({"success": True, "message": "Parol muvaffaqiyatli o‘zgartirildi!"})
        else:
            errors = form.errors.as_json()
            return JsonResponse({"success": False, "message": "Forma noto‘g‘ri to‘ldirildi.", "errors": errors},
                                status=400)
    return JsonResponse({"success": False, "message": "GET so‘rovlari qabul qilinmaydi."}, status=405)

@login_required
def resend_verification_email(request):
    user = request.user
    if user.is_email_verified:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Sizning emailingiz allaqachon tasdiqlangan."})
        messages.info(request, "Sizning emailingiz allaqachon tasdiqlangan.")
        return JsonResponse({"success": False, "message": "Email allaqachon tasdiqlangan."}, status=400)

    try:
        verification = EmailVerification.objects.get(user=user)
        if not verification.can_resend():
            remaining_seconds = 120 - int((now() - verification.last_sent_at).total_seconds())
            return JsonResponse({
                "success": False,
                "message": f"Iltimos, {remaining_seconds} soniyadan so‘ng qayta urinib ko‘ring.",
                "reason": "resend_cooldown"
            }, status=429)
        verification.delete()
    except EmailVerification.DoesNotExist:
        pass

    # Yangi tasdiqlash kodi yaratilganda created_at va last_sent_at yangilanadi
    verification = EmailVerification.objects.create(user=user)
    success, message = send_verification_email(user)

    if not success:
        return JsonResponse({"success": False, "message": message, "reason": "send_failed"}, status=500)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "message": message})

    messages.success(request, f"✅ {message}")
    return JsonResponse({"success": True, "message": message})

@login_required
def profile(request):
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    deposit_total = PaymentRequest.objects.filter(user=user, status="approved", transaction_type="deposit").aggregate(Sum('amount'))['amount__sum'] or 0
    withdraw_total = PaymentRequest.objects.filter(user=user, status="approved", transaction_type="withdraw").aggregate(Sum('amount'))['amount__sum'] or 0
    balance = deposit_total - withdraw_total
    presentations = Presentation.objects.filter(user=user).order_by("-created_at")
    ensure_preview_images(presentations)

    context = {
        "base_template": 'authenticated_base.html',
        "user": {
            "username": user.username,
            "email": user.email,
            "balance": float(balance),
            "is_premium": user.is_premium,
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
            "bio": user.bio,
            "is_email_verified": user.is_email_verified,
            "email_notifications": profile.email_notifications,
            "system_notifications": profile.system_notifications,
        },
        "presentations": [
            {
                "id": presentation.id,
                "title": presentation.title,
                "file_url": presentation.file.url if presentation.file else None,
                "preview_image": presentation.preview_image.url if presentation.preview_image else None,
                "template_type": presentation.template_type,
                "created_at": presentation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": presentation.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                "dropbox_url": presentation.dropbox_url if presentation.dropbox_url else None,
            }
            for presentation in presentations
        ]
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_view(request):
    presentations = Presentation.objects.filter(user=request.user).order_by("-created_at")
    ensure_preview_images(presentations)
    return JsonResponse({
        "presentations": [
            {
                "id": presentation.id,
                "title": presentation.title,
                "file_url": presentation.file.url if presentation.file else None,
                "preview_image": presentation.preview_image.url if presentation.preview_image else None,
                "template_type": presentation.template_type,
                "created_at": presentation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": presentation.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                "dropbox_url": presentation.dropbox_url if presentation.dropbox_url else None,
            }
            for presentation in presentations
        ]
    })

@login_required
@require_POST
def save_notification_settings(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    profile.email_notifications = request.POST.get('email_notifications') == 'true'
    profile.system_notifications = request.POST.get('system_notifications') == 'true'
    profile.save()
    return JsonResponse({'success': True, 'message': "Sozlamalar saqlandi!"})

def privacy_policy(request):
    base_template = 'authenticated_base.html' if request.user.is_authenticated else 'base.html'
    context = {'base_template': base_template}
    return render(request, 'users/privacy_policy.html', context)

def terms_of_service(request):
    base_template = 'authenticated_base.html' if request.user.is_authenticated else 'base.html'
    context = {'base_template': base_template}
    return render(request, 'users/terms_of_service.html', context)

@login_required
@require_POST
def delete_profile(request):
    user = request.user
    password = request.POST.get('password')
    if not password:
        return JsonResponse({'success': False, 'message': 'Parolni kiritish majburiy.'}, status=400)

    if not user.check_password(password):
        return JsonResponse({'success': False, 'message': 'Noto‘g‘ri parol.'}, status=400)

    try:
        presentations = Presentation.objects.filter(user=user)
        for presentation in presentations:
            if presentation.dropbox_url:
                dropbox_path = f"/presentations/{user.id}/{presentation.title}_{presentation.id}.pptx"
                delete_from_dropbox(dropbox_path)
            if presentation.file:
                file_path = os.path.join(settings.MEDIA_ROOT, presentation.file.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
            presentation.delete()

        user.profile.delete()
        user.delete()
        logout(request)
        return JsonResponse({'success': True, 'message': 'Profilingiz muvaffaqiyatli o‘chirildi!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def get_notifications(request):
    notifications = request.user.notifications.all()
    return JsonResponse({
        'notifications': [
            {'message': notification.message, 'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
             'is_read': notification.is_read}
            for notification in notifications
        ]
    })