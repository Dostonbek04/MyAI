from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

app_name = "users"

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path("profile/", views.profile, name="profile"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("edit/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("resend-verification-email/", views.resend_verification_email, name="resend_verification_email"),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path("save-notification-settings/", views.save_notification_settings, name="save_notification_settings"),
    path("delete-profile/", views.delete_profile, name="delete_profile"),
    path("get-notifications/", views.get_notifications, name="get_notifications"),
    path("api/users/total/", views.total_users, name="total_users"),
]