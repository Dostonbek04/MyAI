from django.urls import path
from .views import feedback_view, feedback_list, admin_feedback_list, approve_feedback, delete_feedback

app_name = 'feedback'

urlpatterns = [
    path("", feedback_view, name="feedback_view"),
    path("api/feedbacks/", feedback_list, name="feedback_list"),  # React uchun API endpoint
    path("admin/feedbacks/", admin_feedback_list, name="admin_feedback_list"),
    path("admin/feedbacks/approve/<int:feedback_id>/", approve_feedback, name="approve_feedback"),
    path("admin/feedbacks/delete/<int:feedback_id>/", delete_feedback, name="delete_feedback"),
]