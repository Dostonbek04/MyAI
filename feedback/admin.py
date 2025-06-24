from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "message", "is_approved", "created_at")
    search_fields = ("user__username", "email", "message")
    list_filter = ("is_approved", "created_at")
    actions = ["approve_selected"]

    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)
    approve_selected.short_description = "✅ Tanlangan fikrlarni tasdiqlash"

    def email(self, obj):
        return obj.user.email  # ✅ Foydalanuvchining emailini ko‘rsatish
    email.admin_order_field = "user__email"  # ✅ Saralashga imkon berish
    email.short_description = "Email"

    def message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message  # ✅ Fikrni qisqartirib chiqarish
    message.short_description = "Fikr"

    def is_approved(self, obj):
        return obj.is_approved
    is_approved.boolean = True  # ✅ Yashil tasdiq yoki qizil belgi bilan chiqadi
    is_approved.short_description = "Tasdiqlangan"
