"""
voice_chatbot/services.py

Business logic layer cho Voice Chatbot app.
Xử lý: keyword matching, TTS response, conversation log.

Views chỉ gọi các hàm từ đây.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Keyword Matching
# ============================================================

def load_keywords_by_counter() -> dict:
    """
    Load tất cả keywords từ DB, nhóm theo counter_id.

    Returns:
        dict: {counter_id (int): [keyword_str, ...]}
    """
    from backend.voice_chatbot.models import Keyword
    keywords = {}
    for i in range(1, 20):  # Hỗ trợ đến 20 quầy
        words = list(
            Keyword.objects.filter(
                counter_id=i, is_bad_language=False
            ).values_list('word', flat=True)
        )
        if words:
            keywords[i] = words
    return keywords


def find_matching_counter(speech_text: str, keywords: dict) -> Optional[int]:
    """
    Tìm quầy phù hợp dựa trên từ khóa trong văn bản.

    Args:
        speech_text: Văn bản cần so sánh (lowercase)
        keywords: dict từ load_keywords_by_counter()

    Returns:
        counter_id nếu tìm thấy, None nếu không
    """
    text_lower = speech_text.lower()
    for counter_id, word_list in keywords.items():
        for word in word_list:
            if word in text_lower:
                return counter_id
    return None


def contains_bad_language(speech_text: str, counter_id: int) -> bool:
    """Kiểm tra văn bản có chứa từ ngữ không phù hợp không."""
    from backend.voice_chatbot.models import Keyword
    bad_words = Keyword.objects.filter(
        counter_id=counter_id, is_bad_language=True
    ).values_list('word', flat=True)
    text_lower = speech_text.lower()
    return any(word in text_lower for word in bad_words)


def is_end_of_conversation(speech_text: str) -> bool:
    """Kiểm tra người dùng muốn kết thúc hội thoại."""
    end_phrases = ["không", "cảm ơn", "được rồi", "chào", "bai", "ok", "xong"]
    return any(phrase in speech_text.lower() for phrase in end_phrases)


def process_speech_request(speech_text: str) -> dict:
    """
    Xử lý yêu cầu thoại: tìm quầy phù hợp và tạo response.

    Args:
        speech_text: Văn bản được nhận dạng từ giọng nói

    Returns:
        dict: {
            response_text: str,
            counter_id: int|None,
            counter_name: str|None,
            is_end: bool,
            audio_url: str
        }
    """
    from backend.voice_chatbot.models import ConversationLog
    from backend.customer.models import Service
    from core.hardware.audio import save_tts

    import os

    keywords = load_keywords_by_counter()
    response_text = ""
    counter_id = None
    counter_name = None

    # Kiểm tra kết thúc hội thoại trước
    is_end = is_end_of_conversation(speech_text)
    if is_end:
        response_text = "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi. Chào tạm biệt!"
    else:
        # Tìm quầy phù hợp
        counter_id = find_matching_counter(speech_text, keywords)
        if counter_id:
            try:
                service = Service.objects.get(id=counter_id)
                counter_name = service.name
                response_text = f"Vui lòng chọn Quầy {counter_name}. Bạn có cần hỗ trợ thêm gì không?"
            except Service.DoesNotExist:
                response_text = "Không tìm thấy quầy dịch vụ phù hợp."
                counter_id = None
        else:
            is_end = True
            response_text = "Không tìm thấy yêu cầu của bạn, vui lòng liên hệ cán bộ."

    # Tạo file TTS
    audio_file = 'response.mp3'
    audio_path = os.path.join('media/audio', audio_file)
    save_tts(response_text, audio_path)

    # Lưu log
    try:
        ConversationLog.objects.create(
            user_input=speech_text,
            bot_response=response_text,
        )
    except Exception as e:
        logger.warning(f"Không thể lưu ConversationLog: {e}")

    logger.info(f"Speech processed: counter={counter_id}, end={is_end}")
    return {
        'response_text': response_text,
        'counter_id': counter_id,
        'counter_name': counter_name,
        'is_end': is_end,
        'audio_url': f'/media/audio/{audio_file}',
    }


# ============================================================
# Keyword management
# ============================================================

def update_keywords_for_counter(
    counter_id: int,
    new_keywords: list[str],
    new_bad_keywords: list[str],
) -> str:
    """
    Cập nhật danh sách từ khóa cho một quầy.

    Returns:
        str: Thông báo kết quả
    """
    from backend.voice_chatbot.models import Keyword
    from backend.customer.models import Service

    counter = Service.objects.get(pk=counter_id)

    current_kws = set(
        Keyword.objects.filter(counter=counter, is_bad_language=False)
        .values_list('word', flat=True)
    )
    current_bad = set(
        Keyword.objects.filter(counter=counter, is_bad_language=True)
        .values_list('word', flat=True)
    )

    new_kw_set = set(new_keywords)
    new_bad_set = set(new_bad_keywords)

    # Xóa từ khóa không còn trong danh sách mới
    to_delete = (current_kws - new_kw_set) | (current_bad - new_bad_set)
    Keyword.objects.filter(counter=counter, word__in=to_delete).delete()

    # Thêm từ khóa mới
    for word in new_kw_set - current_kws:
        Keyword.objects.create(word=word, counter=counter, is_bad_language=False)

    for word in new_bad_set - current_bad:
        Keyword.objects.create(word=word, counter=counter, is_bad_language=True)

    logger.info(f"Updated keywords for counter {counter_id}")
    return "Đã cập nhật danh sách từ khóa."
