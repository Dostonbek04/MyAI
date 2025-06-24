from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import PaymentRequest


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "created_at", "approve_button", "reject_button")
    list_filter = ("status",)

    def approve_button(self, obj):
        if obj.status == "pending":
            url = reverse("payments:approve_payment", args=[obj.id])
            return format_html(f'<a class="button" href="{url}">✅ Tasdiqlash</a>')
        return "✔️"

    def reject_button(self, obj):
        if obj.status == "pending":
            url = reverse("payments:reject_payment", args=[obj.id])
            return format_html(f'<a class="button" href="{url}" style="color:red;">❌ Rad etish</a>')
        return "❌"

    approve_button.short_description = "Tasdiqlash"
    reject_button.short_description = "Rad etish"