"""
core/hardware/printer.py

Xử lý máy in nhiệt XP-58C thông qua Windows Print API (win32print).
ESC/POS protocol — in số thứ tự bằng tiếng Việt không dấu.

Usage:
    from core.hardware.printer import print_ticket
    print_ticket(ticket_number='A001', counter='Hộ tịch')
"""

import win32print
import unicodedata
import logging

logger = logging.getLogger(__name__)

PRINTER_NAME = "XP-58C"

# ============================================================
# Text conversion
# ============================================================

def convert_to_latin1(text: str) -> str:
    """
    Chuyển đổi văn bản tiếng Việt có dấu sang không dấu (Latin-1).
    Máy in nhiệt XP-58C chỉ hỗ trợ CP437/Latin-1.
    """
    vietnamese_latin1_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd', 'Đ': 'D',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        # Uppercase
        'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
        'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
        'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
        'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
        'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
        'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
        'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
        'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
        'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
        'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
        'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
    }
    result = ''
    for char in text:
        result += vietnamese_latin1_map.get(char, char)
    return result.upper()


# ============================================================
# ESC/POS commands
# ============================================================

ESC_INIT          = b'\x1b\x40'        # Khởi tạo máy in
ESC_CODEPAGE      = b'\x1b\x74\x00'    # Bảng mã CP437/Latin1
ESC_ALIGN_CENTER  = b'\x1b\x61\x01'    # Căn giữa
ESC_ALIGN_LEFT    = b'\x1b\x61\x00'    # Căn trái
ESC_BOLD_ON       = b'\x1b\x45\x01'    # Bật chữ đậm
ESC_BOLD_OFF      = b'\x1b\x45\x00'    # Tắt chữ đậm
ESC_SIZE_DOUBLE   = b'\x1d\x21\x11'    # Kích thước gấp đôi
ESC_SIZE_NORMAL   = b'\x1d\x21\x00'    # Kích thước bình thường
ESC_FEED          = b'\n\n\n\n'         # Đẩy giấy
ESC_CUT           = b'\x1d\x56\x41\x10' # Cắt giấy một phần


# ============================================================
# Public API
# ============================================================

def get_available_printers() -> list[str]:
    """Trả về danh sách tên máy in đang cài đặt trên Windows."""
    return [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]


def print_ticket(ticket_number: str = 'A001', counter: str = 'Ho tich',
                 printer_name: str = PRINTER_NAME) -> None:
    """
    In phiếu số thứ tự ra máy in nhiệt XP-58C.

    Args:
        ticket_number: Số thứ tự, vd: 'A001', '1001'
        counter:       Tên quầy, vd: 'Hộ tịch', 'Hôn nhân'
        printer_name:  Tên máy in Windows (default: XP-58C)

    Raises:
        ValueError: Nếu không tìm thấy máy in
        Exception:  Lỗi trong quá trình in
    """
    printers = get_available_printers()
    if printer_name not in printers:
        raise ValueError(
            f"Không tìm thấy máy in '{printer_name}'. "
            f"Máy in đang có: {printers}"
        )

    content = f"""
SÔ THÚ TÚ
{ticket_number}
------------------------
QUÂY {counter}
"""
    latin1_content = convert_to_latin1(content)

    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(hPrinter, 1, ("In vé", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)

        # Init commands
        for cmd in [ESC_INIT, ESC_CODEPAGE, ESC_ALIGN_CENTER,
                    ESC_SIZE_DOUBLE, ESC_BOLD_ON]:
            win32print.WritePrinter(hPrinter, cmd)

        # Content
        win32print.WritePrinter(hPrinter, latin1_content.encode('latin1'))

        # Post commands
        for cmd in [ESC_BOLD_OFF, ESC_SIZE_NORMAL, ESC_FEED, ESC_CUT]:
            win32print.WritePrinter(hPrinter, cmd)

        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        logger.info(f"In thành công: số {ticket_number} - quầy {counter}")

    except Exception as e:
        logger.error(f"Lỗi in vé: {e}")
        raise
    finally:
        win32print.ClosePrinter(hPrinter)
