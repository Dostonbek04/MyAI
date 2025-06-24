from django.urls import path
from .views import payment_request_view, approve_payment, reject_payment, admin_payments
from . import views
from django.urls import path
from payments.views import approve_payment, reject_payment
from .views import profile_payments

app_name = "payments"  # 🔹 Bu qator bo‘lishi shart!

urlpatterns = [
    path("request/", payment_request_view, name="request_payment"),
    path("admin/payments/", admin_payments, name="admin_payments"),
    path('admin/approve/<int:payment_id>/', approve_payment, name="approve_payment"),
    path('admin/reject/<int:payment_id>/', reject_payment, name="reject_payment"),
    path("approve/<int:payment_id>/", approve_payment, name="approve_payment"),
    path("reject/<int:payment_id>/", reject_payment, name="reject_payment"),
    path("payments/", profile_payments, name="profile_payments"),
]
