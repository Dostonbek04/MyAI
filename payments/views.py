from django.db.models import Sum
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect
from .forms import PaymentRequestForm
from .utils import send_telegram_message
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import PaymentRequest

ADMIN_CARD_NUMBER = "9860 1201 2413 4186"  # 💳 Admin kartasi

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import PaymentRequest

@login_required
@require_GET
def profile_payments(request):
    """📜 Foydalanuvchining to‘lov tarixi API yoki sahifa"""
    payments = PaymentRequest.objects.filter(user=request.user).order_by("-created_at")

    # Accept header'ni tekshirish
    if 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            "success": True,
            "payments": [
                {
                    "id": payment.id,
                    "amount": float(payment.amount),
                    "status": payment.status,
                    "transaction_type": payment.transaction_type,
                    "receipt_url": payment.receipt.url if payment.receipt else None,
                    "created_at": payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "reviewed_by": payment.reviewed_by.username if payment.reviewed_by else None,
                }
                for payment in payments
            ]
        })

    # HTML sahifasini render qilish
    context = {
        'payments': payments,
    }
    return render(request, 'users/profile_payments.html', context)

@login_required
def get_user_balance(request):
    """Foydalanuvchining balansini hisoblash va qaytarish"""
    deposit_total = PaymentRequest.objects.filter(user=request.user, status="approved", transaction_type="deposit").aggregate(Sum('amount'))['amount__sum'] or 0
    withdraw_total = PaymentRequest.objects.filter(user=request.user, status="approved", transaction_type="withdraw").aggregate(Sum('amount'))['amount__sum'] or 0
    balance = deposit_total - withdraw_total
    return JsonResponse({
        "success": True,
        "balance": float(balance)
    })

@login_required
def payment_request_view(request):
    """💳 Foydalanuvchi balansni to‘ldirish uchun so‘rov yuboradi"""
    # Accept header'ni tekshirish (AJAX yoki oddiy so‘rov)
    is_ajax = 'application/json' in request.headers.get('Accept', '')

    if request.method == "POST":
        form = PaymentRequestForm(request.POST, request.FILES)
        if form.is_valid():
            payment_request = form.save(commit=False)
            payment_request.user = request.user
            payment_request.status = "pending"
            payment_request.save()

            # 🔹 Bot orqali xabar yuborish
            try:
                message = (
                    f"📢 <b>Yangi to‘lov so‘rovi!</b>\n"
                    f"👤 Foydalanuvchi: <b>{request.user.username}</b>\n"
                    f"💰 Miqdor: <b>${payment_request.amount}</b>\n"
                    f"📅 Sana: {payment_request.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"🔗 <a href='{request.build_absolute_uri(payment_request.receipt.url)}'>📄 Chekni Ko‘rish</a>\n\n"
                    f"Eltimos Tasdiqlang va chekning faoligi 24 soatdan oshmaganligiga etibor bering!\n\n\n"
                )
                send_telegram_message(message)
            except Exception as e:
                print(f"Telegram xabar yuborishda xato: {str(e)}")

            # AJAX bo‘lsa JSON qaytar, aks holda redirect
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "message": "✅ So‘rovingiz qabul qilindi! Admin tasdiqlaganidan keyin balansga tushadi.",
                    "redirect_url": "/users/profile"
                })
            return redirect('users:profile')  # HTML sahifaga o‘tish

        else:
            # Forma xatolari
            if is_ajax:
                errors = form.errors.as_json()
                return JsonResponse({
                    "success": False,
                    "message": "Forma noto‘g‘ri to‘ldirildi.",
                    "errors": errors
                }, status=400)
            # HTML sahifada xatoni ko‘rsatish uchun
            return render(request, 'payments/payment_request.html', {
                'form': form,
                'error': "Forma noto‘g‘ri to‘ldirildi."
            })

    else:
        # GET so‘rovi
        if is_ajax:
            return JsonResponse({
                "success": True,
                "card_number": ADMIN_CARD_NUMBER
            })
        # HTML formasini ko‘rsatish
        form = PaymentRequestForm()
        return render(request, 'payments/payment_request.html', {
            'form': form,
            'card_number': ADMIN_CARD_NUMBER
        })

@user_passes_test(lambda u: u.is_staff)
@login_required
def approve_payment(request, payment_id):
    """✅ To‘lovni tasdiqlash"""
    try:
        payment = get_object_or_404(PaymentRequest, id=payment_id, status="pending")
        payment.status = "approved"
        payment.reviewed_by = request.user
        payment.save()
        messages.success(request, f"{payment.user.username} uchun to‘lov muvaffaqiyatli tasdiqlandi!")
    except Exception as e:
        messages.error(request, f"To‘lovni tasdiqlashda xatolik: {str(e)}")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/payments/paymentrequest/'))

@user_passes_test(lambda u: u.is_staff)
@login_required
def reject_payment(request, payment_id):
    """❌ To‘lovni rad etish"""
    try:
        payment = get_object_or_404(PaymentRequest, id=payment_id, status="pending")
        payment.status = "rejected"
        payment.reviewed_by = request.user
        payment.save()
        messages.success(request, f"{payment.user.username} uchun to‘lov muvaffaqiyatli rad etildi.")
    except Exception as e:
        messages.error(request, f"To‘lovni rad etishda xatolik: {str(e)}")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/payments/paymentrequest/'))

@user_passes_test(lambda u: u.is_staff)
@login_required
def admin_payments(request):
    """📌 Admin barcha to‘lov so‘rovlarini ko‘radi"""
    payments = PaymentRequest.objects.filter(status="pending").order_by("-created_at")

    return JsonResponse({
        "success": True,
        "payments": [
            {
                "id": payment.id,
                "user": payment.user.username,
                "amount": float(payment.amount),
                "status": payment.status,
                "transaction_type": payment.transaction_type,
                "receipt_url": payment.receipt.url if payment.receipt else None,
                "created_at": payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for payment in payments
        ]
    })