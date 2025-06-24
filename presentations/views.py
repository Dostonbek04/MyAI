from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.base import ContentFile
from openai import OpenAI
from .presentationsTemplates.templates.light_templates import create_light_template, LIGHT_TEMPLATES
from .presentationsTemplates.templates.dark_templates import create_dark_template, DARK_TEMPLATES
from .presentationsTemplates.templates.professional_templates import create_professional_template, PROFESSIONAL_TEMPLATES
from .models import Presentation, PresentationImage
from .utils import create_template_preview
import os
import json
import io
import requests
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Lotin harflariga moslashtirish uchun funksiya
def to_latin(text):
    replacements = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'J', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': '', 'Ы': 'I', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    for cyrillic, latin in replacements.items():
        text = text.replace(cyrillic, latin)
    return text

import logging
import traceback
import sys
import os

# Logging sozlamasi
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Faylga yozish uchun handler (UTF-8 bilan)
file_handler = logging.FileHandler('debug.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Konsolga yozish uchun handler (Unicode xatolarini oldini olish uchun)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

@login_required
def select_template(request):
    logger.debug("select_template view ishga tushdi")
    presentation_data = request.session.get("presentation_data")
    logger.debug(f"presentation_data: {presentation_data}")
    if not presentation_data:
        logger.error("presentation_data topilmadi")
        messages.error(request, "Avval taqdimot ma’lumotlarini kiriting.")
        return redirect("presentations:generate_titles")

    if request.method == "POST":
        try:
            logger.debug("POST so‘rov keldi")
            topic = presentation_data.get('topic')
            subject = presentation_data.get('subject')
            list_count = int(presentation_data.get('list_count', 8))
            with_images = presentation_data.get('with_images', False)
            template_type = request.POST.get('template_type', 'light')
            style_index = request.POST.get('style_index', '-1')
            try:
                style_index = int(style_index)
            except (ValueError, TypeError):
                style_index = -1
            logger.info(f"Style index: {style_index}, Template type: {template_type}")
            titles = request.session.get('titles', [])
            # Unicode xatolarini oldini olish uchun titles ni tozalash
            titles = [str(title).encode('ascii', 'ignore').decode('ascii') for title in titles]
            logger.debug(f"titles: {titles}")

            if not topic or not titles or not subject:
                logger.error("Mavzu, fan yoki sarlavhalar topilmadi")
                return JsonResponse({"error": "Mavzu, fan yoki sarlavhalar topilmadi"}, status=400)

            presentation = Presentation(user=request.user, title=topic)
            logger.debug("Presentation ob'ekti yaratildi")
            presentation.save()

            subject_lower = subject.lower()
            if "anatomiya" in subject_lower or "biologiya" in subject_lower:
                context = "(inson tanasidagi anatomik tuzilma)"
                focus_instruction = "faqat anatomik jihatlarga e’tibor ber"
            elif "matematika" in subject_lower:
                context = "(sanoq sonlari, raqamlar)"
                focus_instruction = "faqat raqamlar va hisob-kitoblar haqida yoz"
            else:
                context = ""
                focus_instruction = ""

            slide_texts = []
            for i, title in enumerate(titles[:-1]):
                try:
                    logger.debug(f"Slide {i} uchun matn generatsiya qilinmoqda")
                    prompt = f"Mavzu: {topic} {context}. Sarlavha: {title}. Fan: {subject}. Ushbu mavzu va fanga qat’iy rioya qilib, rasmiy uslubda 2-3 gapdan iborat qisqa ma’lumot yoz (10-20 so‘z). Mavzudan chetga chiqma, {focus_instruction}. O‘zbek tilida, faqat lotin harflari ishlat. Turkcha harflarni ishlatma, faqat o‘zbekcha bo‘lsin."
                    response = client.chat.completions.create(
                        model="gpt-4-0125-preview",
                        messages=[{"role": "system", "content": "Siz taqdimotlar uchun qisqa, rasmiy va aniq matnlar generatsiya qiluvchi yordamchisiz."}, {"role": "user", "content": prompt}],
                        max_tokens=300,
                        temperature=0.6
                    )
                    text = response.choices[0].message.content.strip()
                    text = to_latin(text)
                    slide_texts.append(text)
                    logger.debug(f"Slide {i} matni: {text}")
                except Exception as e:
                    logger.error(f"Matn generatsiyasida xato (Slide {i}): {str(e)}\n{traceback.format_exc()}")
                    return JsonResponse({"error": f"OpenAI matn generatsiyasida xato: {str(e)}"}, status=500)

            try:
                logger.debug("Xulosa matni generatsiya qilinmoqda")
                context_text = "\n".join([f"Sarlavha: {title}\nMatn: {text}" for title, text in zip(titles[:-1], slide_texts)])
                prompt = f"Mavzu: {topic} {context}. Fan: {subject}. Quyidagi sarlavhalar va matnlarga asoslanib, xulosa sifatida 3-4 gapdan iborat qisqa matn yoz (20-30 so‘z). Mavzudan chetga chiqma, {focus_instruction}. O‘zbek tilida, faqat lotin harflari ishlat. Turkcha harflarni ishlatma, faqat o‘zbekcha bo‘lsin.\n\n{context_text}"
                response = client.chat.completions.create(
                    model="gpt-4-0125-preview",
                    messages=[{"role": "system", "content": "Siz taqdimotlar uchun qisqa, rasmiy va aniq xulosa matnlari generatsiya qiluvchi yordamchisiz."}, {"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.6
                )
                conclusion_text = response.choices[0].message.content.strip()
                conclusion_text = to_latin(conclusion_text)
                slide_texts.append(conclusion_text)
                logger.debug(f"Xulosa matni: {conclusion_text}")
            except Exception as e:
                logger.error(f"Xulosa generatsiyasida xato: {str(e)}\n{traceback.format_exc()}")
                return JsonResponse({"error": f"Xulosa generatsiyasida xato: {str(e)}"}, status=500)

            image_paths = []
            image_count = list_count // 2
            if with_images:
                for i in range(list_count):
                    if i % 2 == 0 and len(image_paths) < image_count:
                        try:
                            logger.debug(f"Slide {i} uchun rasm generatsiya qilinmoqda")
                            prompt = f"Qisqa matn: {slide_texts[i]}. Ushbu matn asosida rasm generatsiya qil."
                            response = client.images.generate(
                                prompt=prompt,
                                n=1,
                                size="256x256"
                            )
                            image_url = response.data[0].url
                            presentation_image = PresentationImage(presentation=presentation, slide_number=i + 1)
                            presentation_image.image.save(
                                f"{topic}_slide_{i + 1}_image_{len(image_paths) + 1}.jpg",
                                ContentFile(requests.get(image_url).content)
                            )
                            presentation_image.save()
                            image_paths.append(presentation_image.image.path)
                            logger.debug(f"Slide {i} uchun rasm saqlandi: {image_paths[-1]}")
                        except Exception as e:
                            logger.error(f"Rasm generatsiyasida xato (Slide {i}): {str(e)}\n{traceback.format_exc()}")
                            return JsonResponse({"error": f"OpenAI rasm generatsiyasida xato: {str(e)}"}, status=500)
                    else:
                        image_paths.append(None)
            else:
                image_paths = [None] * list_count
            logger.debug(f"image_paths: {image_paths}")

            if len(slide_texts) != list_count or len(image_paths) != list_count:
                logger.error(f"Slide sonlari mos kelmadi: slide_texts={len(slide_texts)}, image_paths={len(image_paths)}, list_count={list_count}")
                return JsonResponse({"error": "Slaydlar soni mos kelmadi"}, status=400)

            ppt = None
            try:
                logger.debug("Shablon yaratilmoqda")
                if template_type == "light":
                    ppt = create_light_template(topic, titles, slide_texts, image_paths, list_count, style_index, with_images)
                elif template_type == "dark":
                    ppt = create_dark_template(topic, titles, slide_texts, image_paths, list_count, style_index, with_images)
                elif template_type == "professional":
                    ppt = create_professional_template(topic, titles, slide_texts, image_paths, list_count, style_index, with_images)
                else:
                    logger.error(f"Noto‘g‘ri shablon turi: {template_type}")
                    return JsonResponse({"error": f"Noto‘g‘ri shablon turi: {template_type}"}, status=400)

                if ppt is None:
                    logger.error(f"Shablon yaratishda xato: {template_type}, style_index={style_index}")
                    return JsonResponse({"error": "Shablon yaratishda xato yuz berdi"}, status=500)
            except Exception as e:
                logger.error(f"Shablon yaratishda xato: {str(e)}\n{traceback.format_exc()}")
                return JsonResponse({"error": f"Shablon yaratishda xato: {str(e)}"}, status=500)

            try:
                logger.debug("PPT fayli saqlanmoqda")
                ppt_io = io.BytesIO()
                ppt.save(ppt_io)
                ppt_io.seek(0)
                presentation.file.save(f"{topic}.pptx", ContentFile(ppt_io.read()))
                presentation.template_type = template_type
                presentation.save()
                logger.debug("PPT fayli saqlandi")
            except Exception as e:
                logger.error(f"PPT faylini saqlashda xato: {str(e)}\n{traceback.format_exc()}")
                return JsonResponse({"error": f"PPT faylini saqlashda xato: {str(e)}"}, status=500)

            request.session.pop('presentation_data', None)
            request.session.pop('titles', None)

            if style_index == -1:
                messages.success(request, "✅ AI bilan taqdimot yaratildi! Shablon tasodifiy tanlandi.")
            else:
                messages.success(request, f"✅ AI bilan taqdimot yaratildi! Tanlangan shablon: {template_type} #{style_index}")

            logger.debug("Taqdimot muvaffaqiyatli yaratildi")
            return JsonResponse({"success": True, "redirect_url": "/users/profile"})
        except Exception as e:
            logger.error(f"Taqdimot yaratishda umumiy xato: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({"error": f"Taqdimot yaratishda xato: {str(e)}"}, status=500)
    else:
        template_types = {
            "dark": DARK_TEMPLATES,
            "light": LIGHT_TEMPLATES,
            "professional": PROFESSIONAL_TEMPLATES
        }

        for template_type, templates in template_types.items():
            for i, template in enumerate(templates):
                try:
                    image_path = create_template_preview(
                        template_name=template["name"],
                        background_color=template["background_color"],
                        text_color=template["text_color"],
                        template_type=template_type
                    )
                    relative_path = os.path.relpath(image_path, settings.MEDIA_ROOT)
                    template["image_path"] = f"/media/{relative_path}"
                except Exception as e:
                    logger.error(f"Rasm yaratishda xato: {template['name']} ({template_type}) - Xato: {str(e)}")

        context = {
            "topic": presentation_data.get('topic'),
            "subject": presentation_data.get('subject'),
            "list_count": presentation_data.get('list_count'),
            "templates": template_types
        }
        return render(request, "presentations/select_template.html", context)

@login_required
def get_template_data(request):
    templates_data = {
        'dark': [],
        'light': [],
        'professional': [],
    }

    for template_type, template_list in [
        ('dark', DARK_TEMPLATES),
        ('light', LIGHT_TEMPLATES),
        ('professional', PROFESSIONAL_TEMPLATES)
    ]:
        for i, template in enumerate(template_list):
            try:
                image_path = create_template_preview(
                    template_name=template['name'],
                    background_color=template['background_color'],
                    text_color=template['text_color'],
                    template_type=template_type
                )
                # `media` so‘zi ikki marta qo‘shilmasligi uchun yo‘lni to‘g‘rilaymiz
                relative_path = os.path.relpath(image_path, "media")
                templates_data[template_type].append({
                    'name': template['name'],
                    'image_path': f"/media/{relative_path}",
                    'background_color': template['background_color'],
                    'text_color': template['text_color'],
                })
            except Exception as e:
                print(f"Shablon qo'shishda xato: {template_type} - {template['name']} - Xato: {str(e)}")

    context = {
        'templates': templates_data,
    }
    return render(request, 'select_template.html', context)

@login_required
def presentation_list(request):
    presentations = Presentation.objects.filter(owner=request.user)
    for presentation in presentations:
        if not presentation.preview_image:
            try:
                presentation.save()
            except Exception as e:
                messages.error(request, f"Preview rasm yaratishda xato: {str(e)}")
    return render(request, "users/profile.html", {
        "presentations": presentations,
        "balance": request.user.profile.balance if hasattr(request.user, 'profile') else 0,
    })

@login_required
def download_presentation(request, presentation_id):
    presentation = get_object_or_404(Presentation, id=presentation_id, owner=request.user)
    return redirect(presentation.file.url)

@login_required
def create_presentation(request):
    if request.method == "POST":
        topic = request.POST.get('topic')
        subject = request.POST.get('subject')
        list_count = int(request.POST.get('list_count', 8))
        with_images = request.POST.get('with_images') == 'on'

        if not topic or not subject:
            messages.error(request, "Iltimos, mavzu va fanni kiriting!")
            return render(request, "presentations/create_presentation.html", {
                "topic": topic,
                "subject": subject,
                "list_count": list_count,
                "with_images": with_images
            })

        request.session['presentation_data'] = {
            'topic': topic,
            'subject': subject,
            'list_count': list_count,
            'with_images': with_images,
        }
        return redirect('presentations:generate_titles')
    else:
        return render(request, "presentations/create_presentation.html", {})

@login_required
def generate_titles(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            topic = request.session.get('presentation_data', {}).get('topic')
            subject = request.session.get('presentation_data', {}).get('subject')
            list_count = int(request.session.get('presentation_data', {}).get('list_count', 8))
            with_images = request.session.get('presentation_data', {}).get('with_images', False)

            if not topic or not subject:
                return JsonResponse({"error": "Mavzu yoki fan kiritilmadi"}, status=400)

            subject_lower = subject.lower()
            if "anatomiya" in subject_lower or "biologiya" in subject_lower:
                context = "(inson tanasidagi anatomik tuzilma)"
            elif "matematika" in subject_lower:
                context = "(sanoq sonlari, raqamlar)"
            else:
                context = ""

            prompt = f"Mavzu: {topic} {context}. Fan: {subject}. Ushbu mavzu va fanga qat’iy rioya qilib, {list_count} ta qisqa sarlavha yoz. Sarlavhalar o‘zaro mantiqiy bog‘liq bo‘lsin, bir butun hikoya sifatida ketma-ket joylashsin (kirish, asosiy qism, xulosa). Har bir sarlavha 5-7 so‘zdan iborat bo‘lsin va bir-biridan farq qilsin, takrorlanmasin. Raqam qo‘shmang. O‘zbek tilida, faqat lotin harflari ishlat. Turkcha harflarni ishlatma, faqat o‘zbekcha bo‘lsin."
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "Siz taqdimot sarlavhalari generatsiya qiluvchi yordamchisiz. Hech qanday raqam qo‘shmang."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            titles = response.choices[0].message.content.strip().split('\n')
            titles = [title.strip() for title in titles if title.strip()]
            titles = titles[:list_count]

            titles = [re.sub(r'^\d+\.\s*', '', title) for title in titles]
            while len(titles) < list_count:
                titles.append(f"Qism {len(titles) + 1}".replace(f"{len(titles) + 1}. ", ""))

            try:
                prompt = f"Mavzu: {topic} {context}. Fan: {subject}. Ushbu mavzu va fanga mos 'Kirish' sarlavhasini chiroyliroq qilib yoz (3-5 so‘z). Aslidan diyarli farq qilmasin va imloviy xatolarni ham tuzatib ber. Raqam qo‘shmang. O‘zbek tilida, faqat lotin harflari ishlat. Turkcha harflarni ishlatma, faqat o‘zbekcha bo‘lsin."
                response = client.chat.completions.create(
                    model="gpt-4-0125-preview",
                    messages=[
                        {"role": "system", "content": "Siz taqdimotlar uchun sarlavhalar generatsiya qiluvchi yordamchisiz. Hech qanday raqam qo‘shmang."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600,
                    temperature=0.7
                )
                titles[0] = response.choices[0].message.content.strip()
            except Exception as e:
                return JsonResponse({"error": f"OpenAI kirish sarlavhasi generatsiyasida xato: {str(e)}"}, status=500)

            titles[-1] = "Xulosa"
            request.session['titles'] = titles

            return JsonResponse({
                "titles": titles,
                "with_images": with_images,
            })
        except Exception as e:
            return JsonResponse({"error": f"Umumiy xato: {str(e)}"}, status=500)
    else:
        presentation_data = request.session.get('presentation_data', {})
        if not presentation_data:
            return redirect('presentations:create_presentation')
        return render(request, "presentations/create_presentation.html", {
            "topic": presentation_data.get('topic'),
            "subject": presentation_data.get('subject'),
            "list_count": presentation_data.get('list_count'),
            "with_images": presentation_data.get('with_images'),
            "generate_titles": True
        })

@login_required
def save_titles(request):
    if request.method == "POST":
        titles = request.POST.getlist('titles')
        if not titles:
            messages.error(request, "Sarlavhalar topilmadi!")
            return redirect('presentations:generate_titles')
        request.session['titles'] = titles
        return redirect('presentations:select_template')
    return redirect('presentations:generate_titles')

@login_required
def delete_presentation(request, presentation_id):
    presentation = get_object_or_404(Presentation, id=presentation_id, owner=request.user)
    if presentation.file:
        file_path = presentation.file.path
        if os.path.exists(file_path):
            os.remove(file_path)

    images = PresentationImage.objects.filter(presentation=presentation)
    for img in images:
        if img.image and os.path.exists(img.image.path):
            os.remove(img.image.path)
        img.delete()

    presentation.delete()
    messages.success(request, "✅ Taqdimot muvaffaqiyatli o‘chirildi!")
    return redirect("users:profile")

# presentations/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import Presentation, Slide

@login_required
@ensure_csrf_cookie
def edit_presentation(request, presentation_id):
    # Taqdimotni bazadan olish
    presentation = get_object_or_404(Presentation, id=presentation_id, user=request.user)
    # Taqdimotga tegishli slaydlarni olish
    slides = presentation.slides.all().order_by('order')
    # Slaydlarni JSON formatida template’ga yuborish
    slides_data = [
        {'id': slide.id, 'title': slide.title, 'content': slide.content}
        for slide in slides
    ]
    return render(request, 'presentations/edit_presentation_canvas.html', {
        'presentation_id': presentation_id,
        'slides_data': slides_data,
        'presentation_title': presentation.title,
    })

@login_required
def save_presentation(request, presentation_id):
    presentation = get_object_or_404(Presentation, id=presentation_id, user=request.user)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slides_data = data.get('slides', [])
            # Eski slaydlarni o‘chirish
            presentation.slides.all().delete()
            # Yangi slaydlarni saqlash
            for i, slide_data in enumerate(slides_data):
                Slide.objects.create(
                    presentation=presentation,
                    title=slide_data['title'],
                    content=slide_data['content'],
                    order=i
                )
            return JsonResponse({'status': 'success', 'message': 'Slaydlar saqlandi'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Faqat POST so‘rovlari qo‘llaniladi'}, status=405)
