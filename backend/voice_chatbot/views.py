# voice_chatbot/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os

from backend.voice_chatbot.models import Keyword, ConversationLog, AllowedHost
from .forms import TextForm, KeywordForm, AllowedHostForm
from .models import Keyword
from backend.customer.models import Service

# Hardware imports — optional, không bắt buộc khi dev local
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False



def index(request):
    return render(request, 'voice_chatbot/index.html')

def listen(request):
    keywords = {i: list(Keyword.objects.filter(counter_id=i).values_list('word', flat=True)) for i in range(1, 12)}

    if request.method == 'POST':
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Bot: Tôi đang lắng nghe...")
            speak('Tôi có thể giúp gì cho bạn')
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio, language="vi-VN")
            print("Bạn: " + text)
            response_text = "Bạn nói: " + text
            print(response_text)

            for counter_id, keyword_list in keywords.items():
                if any(keyword in text for keyword in keyword_list):
                    response_text = f" Vui lòng chọn quầy thủ tục số {counter_id}."
                    speak(response_text)
                    break
            else:
                response_text = "Không tìm thấy yêu cầu của bạn, vui lòng liên hệ cán bộ"
                speak(response_text)

            speak("Bạn còn cần giúp gì nữa không")
            with sr.Microphone() as source:
                print("Bot: Đang lắng nghe phản hồi của bạn...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source)

            try:
                response = recognizer.recognize_google(audio, language="vi-VN")
                print("Bạn: " + response)
                if any(keyword in response for keyword in ["không cần", "không", "cám ơn", "được rồi", "xong", "hông", "Ok"]):
                    speak('Cám ơn. Xin chào và hẹn gặp lại')    
                    return redirect('customer:trang-chu')
                else:
                    return JsonResponse({'response': "Bạn cần giúp gì nữa?"})
            except sr.UnknownValueError:
                print("Bot: Tôi không hiểu bạn nói gì.")
                return JsonResponse({'response': "Bot: Tôi không hiểu bạn nói gì."})
            except sr.RequestError:
                print("Bot: Không thể kết nối đến Google Speech Recognition.")
                return JsonResponse({'response': "Bot: Không thể kết nối đến Google Speech Recognition."})

        except sr.UnknownValueError:
            print("Bot: Tôi không hiểu bạn nói gì.")
            response_text = "Bot: Tôi không hiểu bạn nói gì."
            speak(response_text)
            return JsonResponse({'response': response_text})
        except sr.RequestError:
            print("Bot: Không thể kết nối đến Google Speech Recognition.")
            response_text = "Bot: Không thể kết nối đến Google Speech Recognition."
            speak(response_text)
            return JsonResponse({'response': response_text})

        
def speak(request,text):
    tts = gTTS(text=text, lang="vi")
    file_path = "output.mp3"
    tts.save(file_path)
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()
    
    response = FileResponse(open(file_path, 'rb'))
    os.remove(file_path)  # Xóa tệp sau khi phát xong để tránh dư thừa
    return response
    
def test_audio(request):
    return render(request, 'voice_chatbot/audio.html')

def select_counter(request):
    counter = Service.objects.all()
    return render(request, 'voice_chatbot/select_counter.html', {'counters': counter})
def keyword_check(request, pk):
    response_text = ""
    counter = get_object_or_404(Service, pk=pk)
    
    keywords = list(counter.keywords.values_list('id', 'word', 'is_bad_language'))
    keyword_list = ','.join([keyword[1] for keyword in keywords if not keyword[2]])
    bad_keyword_list = ','.join([keyword[1] for keyword in keywords if keyword[2]])

    if request.method == "POST":
        form = TextForm(request.POST)
        
        if 'check_text' in request.POST and form.is_valid():
            text = form.cleaned_data['text']
            if any(keyword[1] in text for keyword in keywords):
                if any(keyword[1] in text and keyword[2] for keyword in keywords):
                    response_text = "Câu hỏi chứa từ ngữ không phù hợp."
                else:
                    response_text = f"Vui lòng chọn quầy thủ tục số {counter.name}."
            else:
                response_text = "Không có từ khóa phù hợp."
        
        if 'update_keywords' in request.POST:
            new_keywords = [kw.strip() for kw in request.POST.get('keywords').strip().lower().split(',') if kw.strip()]
            new_bad_keywords = [kw.strip() for kw in request.POST.get('bad_keywords').strip().lower().split(',') if kw.strip()]

            current_keywords = set(keyword[1] for keyword in keywords if not keyword[2])
            current_bad_keywords = set(keyword[1] for keyword in keywords if keyword[2])

            new_keywords_set = set(new_keywords)
            new_bad_keywords_set = set(new_bad_keywords)

            to_delete = current_keywords.difference(new_keywords_set).union(current_bad_keywords.difference(new_bad_keywords_set))
            Keyword.objects.filter(counter=counter, word__in=to_delete).delete()

            # Thêm từ khóa mới
            for new_keyword in new_keywords_set.difference(current_keywords):
                Keyword.objects.create(word=new_keyword, counter=counter, is_bad_language=False)
            
            for new_bad_keyword in new_bad_keywords_set.difference(current_bad_keywords):
                Keyword.objects.create(word=new_bad_keyword, counter=counter, is_bad_language=True)

            response_text = "Đã cập nhật danh sách từ khóa."

        return JsonResponse({'response_text': response_text})
    
    form = TextForm()
    
    return render(request, 'voice_chatbot/keyword_check.html', {
        'form': form,
        'counter': counter,
        'keywords': keyword_list,
        'bad_keywords': bad_keyword_list,
    })

def add_keyword(request, pk):
    counter = get_object_or_404(Service, pk=pk)
    new_keywords = [kw.strip() for kw in request.POST.get('new_keywords').strip().lower().split(',')]
    is_bad_language = request.POST.get('is_bad_language') == 'true'
    response_text = ""
    for new_keyword in new_keywords:
        if not new_keyword:
            continue
        elif Keyword.objects.filter(word=new_keyword, counter=counter).exists():
            response_text += f"Từ khóa '{new_keyword}' đã tồn tại trong quầy '{counter.name}'.<br>"
        else:
            Keyword.objects.create(word=new_keyword, counter=counter, is_bad_language=is_bad_language)
            response_text += f"Đã thêm từ khóa '{new_keyword}' vào quầy '{counter.name}'.<br>"
    
    return JsonResponse({'response_text': response_text})

def update_keyword(request, pk):
    keyword_id = request.POST.get('keyword_id')
    updated_keyword = request.POST.get('updated_keyword').strip().lower()
    updated_is_bad_language = request.POST.get('updated_is_bad_language') == 'true'
    if not updated_keyword:
        return JsonResponse({'response_text': "Từ khóa cập nhật không được để trống."})
    
    keyword = Keyword.objects.get(id=keyword_id)
    keyword.word = updated_keyword
    keyword.is_bad_language = updated_is_bad_language
    keyword.save()
    return JsonResponse({'response_text': f"Đã cập nhật từ khóa '{updated_keyword}'."})

def delete_keyword(request, pk):
    keyword_id = request.POST.get('keyword_id')
    Keyword.objects.get(id=keyword_id).delete()
    return JsonResponse({'response_text': "Đã xóa từ khóa."})
# Tạo file âm thanh cho lời chào nếu chưa tồn tại (chỉ khi có gTTS)
greeting_text = "Xin chào! Trung Tâm Phục Vụ Hành Chính Công có thể hỗ trợ gì cho bạn?"
greeting_file = 'greeting.mp3'
greeting_path = os.path.join('media/audio', greeting_file)
if GTTS_AVAILABLE and not os.path.exists(greeting_path):
    try:
        tts = gTTS(greeting_text, lang='vi')
        tts.save(greeting_path)
    except Exception:
        pass


@csrf_exempt
def process_request(request):
    keywords = {i: list(Keyword.objects.filter(counter_id=i, is_bad_language=False).values_list('word', flat=True)) for i in range(1, 12)}
    ket_thuc=''
    if request.method == 'POST':
        data = json.loads(request.body)
        speech_text = data.get('speech_text').lower()
        print(speech_text)
        print("Bạn: " + speech_text)

        response_text = ""

        for counter_id, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in speech_text:
                    counter_name = Service.objects.get(id=counter_id).name
                    # print(f"Từ khóa trùng khớp: {keyword}")
                    # print(f"Quầy: {counter_name}")
                    response_text = f"Vui lòng chọn Quầy {counter_name}. Bạn có cần hỗ trợ thêm gì không?"
                    print(response_text)
                    break
            if response_text:
                break
        else:
            ket_thuc=1
            response_text = "Không tìm thấy yêu cầu của bạn, vui lòng liên hệ cán bộ."

        # Kiểm tra xem cuộc trò chuyện có kết thúc không
        end_phrases = ["không", "cảm ơn", "được rồi","chào","bai"]
        if any(phrase in speech_text.lower() for phrase in end_phrases):
            response_text = "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi. Chào tạm biệt!"
            ket_thuc =1
        # Tạo file âm thanh từ văn bản
        tts = gTTS(response_text, lang='vi')
        audio_file = 'response.mp3'
        audio_path = os.path.join('media/audio', audio_file)
        tts.save(audio_path)

        # Lưu log vào cơ sở dữ liệu
        log = ConversationLog(user_input=speech_text, bot_response=response_text)
        log.save()

        response = {
            'message': response_text,
            'audio_url': f'/media/audio/{audio_file}',
            'ket_thuc': ket_thuc  # Thêm biến ket_thuc vào phản hồi
        }

        return JsonResponse(response)
import csv
from .models import ConversationLog

def export_logs_to_csv():
    logs = ConversationLog.objects.all()
    with open('conversation_logs.csv', 'w', newline='') as csvfile:
        fieldnames = ['user_input', 'bot_response', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for log in logs:
            writer.writerow({'user_input': log.user_input, 'bot_response': log.bot_response, 'timestamp': log.timestamp})
            

# def process_request(request):
#     keywords = {i: list(Keyword.objects.filter(counter_id=i,is_bad_language=False).values_list('word', flat=True)) for i in range(1, 12)}
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         speech_text = data.get('speech_text')
#         print("Bạn: " + speech_text)
#         response_text = ""
#         for counter_id, keyword_list in keywords.items():
#             if any(keyword in speech_text for keyword in keyword_list):
#                 response_text = f"Vui lòng chọn quầy thủ tục số {counter_id}."
#                 print(response_text)
#                 break
#             else:
#                 response_text = "Không tìm thấy yêu cầu của bạn, vui lòng liên hệ cán bộ"

#         # Tạo file âm thanh từ văn bản
#         tts = gTTS(response_text, lang='vi')
#         audio_file = 'response.mp3'
#         audio_path = os.path.join('media/audio', audio_file)
#         tts.save(audio_path)

#         # Lưu log vào cơ sở dữ liệu
#         log = ConversationLog(user_input=speech_text, bot_response=response_text)
#         log.save()

#         response = {
#             'message': response_text,
#             'audio_url': f'/media/audio/{audio_file}'
#         }

#         return JsonResponse(response) 


# views.py
from django.shortcuts import render, redirect
from .forms import AllowedHostForm
from .models import AllowedHost

def manage_allowed_hosts(request):
    if request.method == "POST":
        form = AllowedHostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('voice_chatbot:manage_allowed_hosts')
    else:
        form = AllowedHostForm()

    allowed_hosts = AllowedHost.objects.all()
    return render(request, 'voice_chatbot/manage_allowed_hosts.html', {'form': form, 'allowed_hosts': allowed_hosts})

def delete_allowed_host(request, pk):
    AllowedHost.objects.get(pk=pk).delete()
    return redirect('voice_chatbot:manage_allowed_hosts')