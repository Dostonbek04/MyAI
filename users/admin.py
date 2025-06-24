from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import SiteStatistics

admin.site.register(CustomUser, UserAdmin)

@admin.register(SiteStatistics)
class SiteStatisticsAdmin(admin.ModelAdmin):
    list_display = ("total_users", "new_users_today", "total_presentations", "new_presentations_today", "total_paid_users", "last_payment_amount", "updated_at")
    readonly_fields = ("updated_at",)
