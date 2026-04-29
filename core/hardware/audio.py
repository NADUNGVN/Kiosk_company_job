"""
core/hardware/audio.py

Xử lý text-to-speech (gTTS) và phát âm thanh qua sounddevice/pygame.
Hỗ trợ ưu tiên thiết bị Bluetooth (M108BT) hoặc Headphone.

Usage:
    from core.hardware.audio import speak, play_audio_file

    # Đọc văn bản tiếng Việt
    speak("Xin chào, số thứ tự A001 mời vào quầy Hộ tịch")

    # Phát file MP3 có sẵn
    play_audio_file("media/audio/chao_ban.mp3")
"""

import os
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Tên thiết bị âm thanh ưu tiên
PREFERRED_DEVICE_NAMES = [
    "Headphones (2- M108BT)",       # Loa Bluetooth M108BT
    "Headphones (High Definition Audio Device)",  # Fallback: Headphone onboard
]


# ============================================================
# Internal helpers
# ============================================================

def _find_output_device() -> Optional[int]:
    """
    Tìm ID thiết bị âm thanh đầu ra theo thứ tự ưu tiên.
    Trả về None nếu không tìm thấy.
    """
    try:
        import sounddevice as sd
        devices = sd.query_devices()

        # Ưu tiên 1: M108BT Bluetooth (hostapi 0)
        device_id = next(
            (i for i, d in enumerate(devices)
             if PREFERRED_DEVICE_NAMES[0] in d['name'] and d['hostapi'] == 0),
            None
        )

        # Ưu tiên 2: Headphone High Definition (hostapi 1)
        if device_id is None:
            device_id = next(
                (i for i, d in enumerate(devices)
                 if PREFERRED_DEVICE_NAMES[1] in d['name'] and d['hostapi'] == 1),
                None
            )

        return device_id
    except Exception as e:
        logger.warning(f"Không thể truy vấn thiết bị âm thanh: {e}")
        return None


def _play_with_sounddevice(audio_array, sample_rate: int, device_id: int) -> None:
    """Phát âm thanh qua sounddevice."""
    import sounddevice as sd
    sd.default.device = (None, device_id)
    sd.play(audio_array, samplerate=sample_rate)
    sd.wait()


def _play_with_pygame(file_path: str) -> None:
    """Fallback: phát âm thanh qua pygame."""
    import pygame
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


# ============================================================
# Public API
# ============================================================

def speak(text: str, lang: str = 'vi', slow: bool = False) -> dict:
    """
    Đọc văn bản bằng gTTS và phát qua thiết bị âm thanh.

    Args:
        text: Văn bản cần đọc (tiếng Việt)
        lang: Ngôn ngữ gTTS (default: 'vi')
        slow: Đọc chậm hay không

    Returns:
        dict: {'status': 'success'|'error', 'message': str}
    """
    if not text:
        return {'status': 'error', 'message': 'Text rỗng'}

    try:
        from gtts import gTTS
        from pydub import AudioSegment
        import numpy as np

        tts = gTTS(text, lang=lang, slow=slow)

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            temp_path = f.name
            tts.save(temp_path)

        try:
            audio = AudioSegment.from_mp3(temp_path)
            audio_array = (
                __import__('numpy').array(audio.get_array_of_samples()) / 32768.0
            )
            sample_rate = audio.frame_rate

            device_id = _find_output_device()

            if device_id is not None:
                _play_with_sounddevice(audio_array, sample_rate, device_id)
                logger.info(f"Đã phát TTS qua sounddevice device={device_id}")
                return {'status': 'success', 'message': 'Âm thanh đã phát trên thiết bị chỉ định.'}
            else:
                logger.warning("Không tìm thấy thiết bị ưu tiên, dùng pygame.")
                _play_with_pygame(temp_path)
                return {'status': 'success', 'message': 'Âm thanh đã phát bằng pygame.'}

        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Lỗi TTS: {e}")
        return {'status': 'error', 'message': str(e)}


def save_tts(text: str, output_path: str, lang: str = 'vi') -> bool:
    """
    Tạo file MP3 từ văn bản và lưu vào output_path.

    Args:
        text: Văn bản cần đọc
        output_path: Đường dẫn file MP3 đầu ra
        lang: Ngôn ngữ gTTS

    Returns:
        bool: True nếu thành công
    """
    try:
        from gtts import gTTS
        tts = gTTS(text, lang=lang)
        tts.save(output_path)
        logger.info(f"Đã lưu TTS: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Lỗi lưu TTS: {e}")
        return False


def play_audio_file(file_path: str) -> dict:
    """
    Phát file âm thanh (.mp3) có sẵn qua thiết bị ưu tiên.

    Args:
        file_path: Đường dẫn đến file MP3

    Returns:
        dict: {'status': 'success'|'error', 'message': str}
    """
    if not os.path.exists(file_path):
        return {'status': 'error', 'message': f'File không tồn tại: {file_path}'}

    try:
        from pydub import AudioSegment
        import numpy as np

        audio = AudioSegment.from_mp3(file_path)
        audio_array = np.array(audio.get_array_of_samples()) / 32768.0
        sample_rate = audio.frame_rate

        device_id = _find_output_device()
        if device_id is not None:
            _play_with_sounddevice(audio_array, sample_rate, device_id)
        else:
            _play_with_pygame(file_path)

        return {'status': 'success', 'message': 'Đã phát audio.'}
    except Exception as e:
        logger.error(f"Lỗi phát audio: {e}")
        return {'status': 'error', 'message': str(e)}
