# presentations/urls.py
from django.urls import path
from . import views

app_name = 'presentations'

urlpatterns = [
    # Frontend funksiyalari
    path("download/<int:presentation_id>/", views.download_presentation, name="download_presentation"),
    path("create/", views.create_presentation, name="create_presentation"),
    path("delete/<int:presentation_id>/", views.delete_presentation, name="delete_presentation"),
    path("generate_titles/", views.generate_titles, name="generate_titles"),
    path("select-template/", views.select_template, name="select_template"),
    path("save_titles/", views.save_titles, name="save_titles"),
    path('presentations/template-data/', views.get_template_data, name='get_template_data'),
    path('edit/<int:presentation_id>/', views.edit_presentation, name='edit_presentation'),
    path('save/<int:presentation_id>/', views.save_presentation, name='save_presentation'),
]