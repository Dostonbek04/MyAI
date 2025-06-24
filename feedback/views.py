# feedback/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect
from .forms import FeedbackForm
from .models import Feedback

@login_required
def feedback_view(request):
    """📝 Foydalanuvchi fikrini saqlash"""
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.email = request.user.email
            feedback.save()
            messages.success(request, "✅ Fikringiz qabul qilindi!")
            return redirect('feedback_list')
        else:
            messages.error(request, "❌ Xatolik yuz berdi! Iltimos, qaytadan urinib ko‘ring.")
            return render(request, 'feedback/feedback_form.html', {'form': form})
    else:
        form = FeedbackForm()
    return render(request, 'feedback/feedback_form.html', {'form': form})

@login_required
def feedback_list(request):
    """Faqat tasdiqlangan feedbacklarni foydalanuvchilar uchun ko‘rsatish."""
    feedbacks = Feedback.objects.filter(is_approved=True)
    context = {
        'feedbacks': feedbacks,
    }
    return render(request, 'feedback/feedback_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_feedback_list(request):
    """Admin barcha sharhlarni ko‘radi va boshqaradi."""
    feedbacks = Feedback.objects.all()
    context = {
        'feedbacks': feedbacks,
    }
    return render(request, 'feedback/admin_feedback_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def approve_feedback(request, feedback_id):
    """Admin sharhni tasdiqlaydi."""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    feedback.is_approved = True
    feedback.save()
    messages.success(request, "Fikr tasdiqlandi!")
    return redirect('admin_feedback_list')

@user_passes_test(lambda u: u.is_staff)
def delete_feedback(request, feedback_id):
    """Admin sharhni o‘chiradi."""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    feedback.delete()
    messages.success(request, "Fikr o‘chirildi!")
    return redirect('admin_feedback_list')