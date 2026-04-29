"""
QRcodes/services.py

Business logic layer cho QRcodes app.
Xử lý: parse CCCD (1/2/3 người), ghi Excel log, mail merge Word.

Views chỉ gọi các hàm từ đây.
"""

import os
import logging
from datetime import datetime

from django.conf import settings
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

MEDIA_ROOT = settings.MEDIA_ROOT


# ============================================================
# CCCD Parsing (dùng chung với customer.services)
# ============================================================

def parse_cccd_fields(raw_string: str) -> dict:
    """
    Parse chuỗi CCCD thành dict các trường.
    Hỗ trợ cả định dạng '|' và '*' separator.

    Returns:
        dict: {so_cccd, ho_va_ten, ngay_sinh, gioi_tinh,
               dia_chi, ngay_cap, thanh_pho}
    """
    raw = raw_string.strip().replace('|', '*')
    parts = raw.split('*')

    if len(parts) < 7:
        raise ValueError(f"Chuỗi CCCD không hợp lệ: chỉ có {len(parts)} trường")

    def parse_date(s: str) -> str:
        try:
            return datetime.strptime(s, "%d%m%Y").strftime("%d/%m/%Y")
        except ValueError:
            return s

    dia_chi = parts[5].replace('\x00', '')
    thanh_pho = dia_chi.split(',')[-1].strip().replace('\x00', '')

    return {
        'so_cccd': parts[0].replace('\x00', ''),
        'ho_va_ten': parts[2].upper(),
        'ngay_sinh': parse_date(parts[3]),
        'gioi_tinh': parts[4].replace('\x00', ''),
        'dia_chi': dia_chi,
        'ngay_cap': parse_date(parts[6]).replace('\x00', ''),
        'thanh_pho': thanh_pho,
    }


# ============================================================
# Excel Logging
# ============================================================

def append_to_excel(file_path: str, row_data: list) -> bool:
    """
    Thêm một hàng dữ liệu vào file Excel hiện có (Sheet1).

    Args:
        file_path: Đường dẫn tuyệt đối đến file .xlsx
        row_data: List các giá trị cần ghi vào hàng mới

    Returns:
        bool: True nếu thành công
    """
    try:
        wb = load_workbook(filename=file_path)
        ws = wb['Sheet1']
        ws.append(row_data)
        wb.save(filename=file_path)
        logger.info(f"Excel updated: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Lỗi ghi Excel {file_path}: {e}")
        return False


def log_don_1_nguoi(cccd: dict) -> bool:
    """Ghi log Excel cho đơn 1 người."""
    file_path = os.path.join(MEDIA_ROOT, 'QRcodes/reports/don_1_nguoi/data.xlsx')
    thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M")
    row = [
        cccd['so_cccd'], '', cccd['ho_va_ten'],
        cccd['gioi_tinh'], cccd['dia_chi'],
        cccd['ngay_cap'], cccd['thanh_pho'], thoi_gian,
    ]
    return append_to_excel(file_path, row)


def log_don_2_nguoi(cccd1: dict, cccd2: dict) -> bool:
    """Ghi log Excel cho đơn 2 người (ket_hon, khai_tu...)."""
    file_path = os.path.join(MEDIA_ROOT, 'QRcodes/reports/don_2_nguoi/2_cccd.xlsx')
    thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M")
    row = [
        cccd1['so_cccd'], cccd1['ho_va_ten'], cccd1['ngay_sinh'],
        cccd1['gioi_tinh'], cccd1['dia_chi'], cccd1['ngay_cap'],
        cccd2['so_cccd'], cccd2['ho_va_ten'], cccd2['ngay_sinh'],
        cccd2['gioi_tinh'], cccd2['dia_chi'], cccd2['ngay_cap'],
        thoi_gian,
    ]
    return append_to_excel(file_path, row)


def log_trich_luc_ho_tich(cccd: dict, loai_don: str, so_luong: str) -> bool:
    """Ghi log Excel cho trích lục hộ tịch."""
    file_path = os.path.join(
        MEDIA_ROOT, 'QRcodes/reports/data/trich_luc_ho_tich/trich_luc_ho_tich.xlsx'
    )
    thoi_gian = datetime.now().strftime("%d/%m/%Y")
    row = [
        '',
        thoi_gian,
        f"{cccd['ho_va_ten']}, Số CCCD {cccd['so_cccd']}",
        loai_don,
        '',
        so_luong,
    ]
    return append_to_excel(file_path, row)


# ============================================================
# Session helpers
# ============================================================

def build_session_data_1(cccd: dict) -> dict:
    """Tạo dict lưu vào session['scan_data_1']."""
    return {
        'so_cccd': cccd['so_cccd'],
        'so_cmnd_cu': '',
        'ho_va_ten': cccd['ho_va_ten'],
        'ngay_sinh': cccd['ngay_sinh'],
        'gioi_tinh': cccd['gioi_tinh'],
        'dia_chi': cccd['dia_chi'],
        'ngay_cap': cccd['ngay_cap'],
        'thanh_pho': cccd['thanh_pho'],
    }


def build_session_data_2(cccd: dict) -> dict:
    """Tạo dict lưu vào session['scan_data_2'] (người thứ 2)."""
    return {
        'so_cccd_2': cccd['so_cccd'],
        'so_cmnd_cu_2': '',
        'ho_va_ten_2': cccd['ho_va_ten'],
        'ngay_sinh_2': cccd['ngay_sinh'],
        'gioi_tinh_2': cccd['gioi_tinh'],
        'dia_chi_2': cccd['dia_chi'],
        'ngay_cap_2': cccd['ngay_cap'],
        'thanh_pho_2': cccd['thanh_pho'],
    }
