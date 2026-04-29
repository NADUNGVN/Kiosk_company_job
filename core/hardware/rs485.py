"""
core/hardware/rs485.py

Đọc tín hiệu cảm biến phát hiện người qua RS485 (COM port).
Khi phát hiện người ($0001#) → phát âm "Chào bạn".
Khi người rời đi ($0000#) → phát âm "Tạm biệt".

Hardware: CH340 USB-Serial (VID=1a86, PID=7523), baud 9600.

Usage:
    from core.hardware.rs485 import RS485Sensor

    sensor = RS485Sensor()
    sensor.start()   # Non-blocking, chạy trong thread riêng
    sensor.stop()
"""

import serial
import serial.tools.list_ports
import threading
import logging
import os
from typing import Optional, Callable

from core.hardware.audio import play_audio_file, save_tts

logger = logging.getLogger(__name__)

# ============================================================
# Config
# ============================================================

RS485_VID = '1a86'   # CH340 USB-Serial chip
RS485_PID = '7523'

BAUD_RATE  = 9600
BYTE_SIZE  = serial.EIGHTBITS
PARITY     = serial.PARITY_NONE
STOP_BITS  = serial.STOPBITS_ONE
TIMEOUT    = 1  # seconds

AUDIO_DIR  = 'media/audio'
CHAO_BAN   = os.path.join(AUDIO_DIR, 'chao_ban.mp3')
TAM_BIET   = os.path.join(AUDIO_DIR, 'tam_biet.mp3')

SIGNAL_ON  = '$0001#'   # Người tiến vào
SIGNAL_OFF = '$0000#'   # Người rời đi


# ============================================================
# Helpers
# ============================================================

def find_com_port(vid: str = RS485_VID, pid: str = RS485_PID) -> Optional[str]:
    """
    Tìm COM port của thiết bị RS485 theo VID/PID.

    Returns:
        str tên port (vd: 'COM3') hoặc None nếu không tìm thấy.
    """
    for port in serial.tools.list_ports.comports():
        if port.vid is not None and port.pid is not None:
            if hex(port.vid)[2:] == vid and hex(port.pid)[2:] == pid:
                return port.device
    return None


def ensure_audio_files() -> None:
    """
    Tạo file MP3 chào/tạm biệt nếu chưa tồn tại.
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if not os.path.exists(CHAO_BAN):
        save_tts("Chào bạn", CHAO_BAN)
        logger.info(f"Đã tạo: {CHAO_BAN}")
    if not os.path.exists(TAM_BIET):
        save_tts("Tạm biệt", TAM_BIET)
        logger.info(f"Đã tạo: {TAM_BIET}")


# ============================================================
# RS485Sensor class
# ============================================================

class RS485Sensor:
    """
    Quản lý vòng đọc tín hiệu RS485 trong background thread.

    Callbacks:
        on_person_enter: Gọi khi có người ($0001#)
        on_person_leave: Gọi khi người rời ($0000#)
    """

    def __init__(
        self,
        on_person_enter: Optional[Callable] = None,
        on_person_leave: Optional[Callable] = None,
    ):
        self.on_person_enter = on_person_enter or self._default_enter
        self.on_person_leave = on_person_leave or self._default_leave
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._signal_on = False

    # ------ Default callbacks ------

    def _default_enter(self):
        play_audio_file(CHAO_BAN)

    def _default_leave(self):
        play_audio_file(TAM_BIET)

    # ------ Public methods ------

    def start(self) -> bool:
        """
        Khởi động đọc RS485 trong background thread.

        Returns:
            True nếu kết nối thành công, False nếu không tìm thấy COM port.
        """
        ensure_audio_files()

        com_port = find_com_port()
        if not com_port:
            logger.warning("RS485: Không tìm thấy COM port (VID=1a86, PID=7523)")
            return False

        logger.info(f"RS485: Kết nối tại {com_port}")
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._read_loop,
            args=(com_port,),
            daemon=True,
            name="RS485-Reader",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Dừng vòng đọc RS485."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("RS485: Đã dừng")

    # ------ Internal loop ------

    def _read_loop(self, com_port: str) -> None:
        try:
            ser = serial.Serial(
                port=com_port,
                baudrate=BAUD_RATE,
                bytesize=BYTE_SIZE,
                parity=PARITY,
                stopbits=STOP_BITS,
                timeout=TIMEOUT,
            )
            logger.info(f"RS485: Đang lắng nghe tín hiệu trên {com_port}...")
            buffer = ""

            while not self._stop_event.is_set():
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data

                    while '$' in buffer and '#' in buffer:
                        start = buffer.find('$')
                        end = buffer.find('#', start)
                        if end == -1:
                            break

                        message = buffer[start:end + 1]
                        buffer = buffer[end + 1:]

                        logger.debug(f"RS485 received: {message}")
                        self._handle_signal(message)

        except serial.SerialException as e:
            logger.error(f"RS485 serial error: {e}")
        finally:
            try:
                ser.close()
            except Exception:
                pass

    def _handle_signal(self, message: str) -> None:
        if message == SIGNAL_ON and not self._signal_on:
            logger.info("RS485: Người vào → Chào bạn")
            self._signal_on = True
            try:
                self.on_person_enter()
            except Exception as e:
                logger.error(f"RS485 enter callback error: {e}")

        elif message == SIGNAL_OFF and self._signal_on:
            logger.info("RS485: Người rời → Tạm biệt")
            self._signal_on = False
            try:
                self.on_person_leave()
            except Exception as e:
                logger.error(f"RS485 leave callback error: {e}")
