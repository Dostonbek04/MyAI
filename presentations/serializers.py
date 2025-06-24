from rest_framework import serializers
from .models import Presentation

class PresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentation
        fields = ['id', 'title', 'slides_data', 'pptx_file', 'pdf_file', 'preview_image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']