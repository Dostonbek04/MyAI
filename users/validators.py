from django.core.exceptions import ValidationError
import re


class CustomPasswordValidator:
    """O‘zimizning parol tekshiruvchi validatorimiz"""

    def validate(self, password, user=None):
        errors = []

        # Kamida 8 ta belgidan iborat bo‘lishi shart
        if len(password) < 8:
            errors.append("Parol kamida 8 ta belgidan iborat bo‘lishi kerak.")

        # Kamida 1 ta katta harf bo‘lishi kerak
        if not any(char.isupper() for char in password):
            errors.append("Parolda kamida 1 ta katta harf bo‘lishi kerak.")

        # Kamida 1 ta son bo‘lishi kerak
        if not any(char.isdigit() for char in password):
            errors.append("Parolda kamida 1 ta son bo‘lishi kerak.")

        # Agar xatolar bo‘lsa, ularni chiqaramiz
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        """Foydalanuvchiga ko‘rsatiladigan xabar"""
        return "Parol kamida 8 ta belgidan iborat bo‘lishi, 1 ta katta harf va 1 ta raqam bo‘lishi kerak."
