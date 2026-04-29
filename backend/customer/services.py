"""
customer/services.py

Business logic layer cho Customer app.
Views chỉ được gọi hàm từ đây — không chứa logic nghiệp vụ.

Phân tầng:
    HTTP Request → views.py → services.py → models.py (DB)
                                          → core.hardware.*
"""

import os
import logging
import qrcode
from datetime import datetime
from collections import defaultdict

from django.urls import reverse
from django.db import transaction
from django.db.models import Max, Count
from django.conf import settings

from backend.customer.models import KhachHang, Service, Employee, ThongKe, DanhSachCho

logger = logging.getLogger(__name__)


# ============================================================
# CCCD Parsing
# ============================================================

def parse_cccd(raw_string: str) -> dict:
    """
    Parse chuỗi dữ liệu từ máy quét CCCD.
    Định dạng: {field1}|{field2}|...  hoặc {field1}*{field2}*...

    Returns:
        dict với các trường: so_cccd, ho_va_ten, ngay_sinh,
                             gioi_tinh, dia_chi, ngay_cap,
                             thanh_pho, ho_ten_cha, ho_ten_me
    Raises:
        ValueError nếu chuỗi không hợp lệ
    """
    raw = raw_string.strip().replace('|', '*')
    fields = raw.split('*')

    if len(fields) < 7:
        raise ValueError(f"CCCD data không đủ trường: {len(fields)} fields")

    try:
        ngay_sinh = datetime.strptime(fields[3], "%d%m%Y").strftime("%d/%m/%Y")
    except ValueError:
        ngay_sinh = fields[3]

    try:
        ngay_cap = datetime.strptime(fields[6], "%d%m%Y").strftime("%d/%m/%Y")
    except ValueError:
        ngay_cap = fields[6]

    dia_chi = fields[5].replace('\x00', '')
    thanh_pho = dia_chi.split(',')[-1].strip()

    return {
        'so_cccd': fields[0].replace('\x00', ''),
        'ho_va_ten': fields[2].upper(),
        'ngay_sinh': ngay_sinh,
        'gioi_tinh': fields[4].replace('\x00', ''),
        'dia_chi': dia_chi,
        'ngay_cap': ngay_cap.replace('\x00', ''),
        'thanh_pho': thanh_pho.replace('\x00', ''),
        'ho_ten_cha': fields[8].replace('\x00', '') if len(fields) > 8 else '',
        'ho_ten_me': fields[9].replace('\x00', '') if len(fields) > 9 else '',
    }


# ============================================================
# Ticket (Số thứ tự)
# ============================================================

def get_next_ticket_number(quay_so: int) -> int:
    """
    Lấy số thứ tự tiếp theo cho quầy quay_so.
    Thread-safe với select_for_update().
    """
    with transaction.atomic():
        service = Service.objects.select_for_update().get(quay_so=quay_so)
        last = KhachHang.objects.filter(service=service).aggregate(
            Max('ticket_number')
        )['ticket_number__max']

        return (last + 1) if last else (service.prefix + 1)


def create_ticket_direct(quay_so: int) -> dict:
    """
    Tạo vé không có thông tin CCCD (lấy số trực tiếp).

    Returns:
        dict: {khachhang, dich_vu, img_name}
    """
    dich_vu = Service.objects.get(quay_so=quay_so)
    ticket_number = get_next_ticket_number(quay_so)

    khachhang = KhachHang.objects.create(
        name='',
        service=dich_vu,
        ticket_number=ticket_number,
        is_calling=False,
    )

    img_name = generate_qr_code(quay_so, khachhang.ticket_number)

    logger.info(f"Direct ticket created: #{ticket_number} - service={dich_vu.name}")
    return {
        'khachhang': khachhang,
        'dich_vu': dich_vu,
        'img_name': img_name,
    }


def create_ticket_with_cccd(quay_so: int, raw_cccd: str) -> dict:
    """
    Tạo vé kèm thông tin CCCD từ chuỗi raw scanner.

    Returns:
        dict: {khachhang, dich_vu, img_name, cccd_data, audio_path}
    """
    from core.hardware.audio import save_tts

    cccd = parse_cccd(raw_cccd)
    dich_vu = Service.objects.get(quay_so=quay_so)
    ticket_number = get_next_ticket_number(quay_so)

    khachhang = KhachHang.objects.create(
        name=cccd['ho_va_ten'],
        dia_chi=cccd['dia_chi'],
        so_cccd=cccd['so_cccd'],
        ngay_sinh=cccd['ngay_sinh'],
        gioi_tinh=cccd['gioi_tinh'],
        ngay_cap=cccd['ngay_cap'],
        service=dich_vu,
        ticket_number=ticket_number,
        is_calling=False,
        ho_ten_cha=cccd.get('ho_ten_cha', ''),
        ho_ten_me=cccd.get('ho_ten_me', ''),
    )

    img_name = generate_qr_code(quay_so, khachhang.ticket_number)

    # TTS phản hồi
    xung_ho = 'Ông' if cccd['gioi_tinh'] == 'Nam' else 'Bà'
    response_text = (
        f"Cảm ơn {xung_ho} {cccd['ho_va_ten']}, "
        f"vui lòng theo dõi số thứ tự trên màn hình."
    )
    audio_file = 'phan_hoi_lay_so.mp3'
    audio_path = os.path.join('media/audio', audio_file)
    save_tts(response_text, audio_path)

    logger.info(f"CCCD ticket created: #{ticket_number} - {cccd['ho_va_ten']}")
    return {
        'khachhang': khachhang,
        'dich_vu': dich_vu,
        'img_name': img_name,
        'cccd_data': cccd,
        'audio_url': f'/media/audio/{audio_file}',
    }


# ============================================================
# QR Code
# ============================================================

def generate_qr_code(quay_so: int, ticket_number: int) -> str:
    """
    Tạo QR code và lưu vào MEDIA_ROOT.

    Returns:
        str: tên file ảnh QR (vd: '1001.png')
    """
    url = reverse('customer:gui-khach-hang', args=[quay_so, ticket_number])
    qr_data = f"https://ready-caring-leech.ngrok-free.app{url}"

    qr_img = qrcode.make(qr_data)
    img_name = f'{ticket_number}.png'
    qr_img.save(os.path.join(settings.MEDIA_ROOT, img_name))

    return img_name


# ============================================================
# Waiting list & Queue management
# ============================================================

def get_waiting_list(service_id: int) -> list:
    """Trả về danh sách khách đang chờ theo dịch vụ."""
    return list(
        KhachHang.objects.filter(
            service_id=service_id,
            is_called=False,
            trang_thai=True,
        ).order_by('ticket_number')
    )


def get_grouped_waiting_list() -> list:
    """
    Nhóm danh sách chờ theo từng dịch vụ.
    Dùng cho màn hình bảng số tổng hợp.

    Returns:
        list of (Service, [KhachHang])
    """
    khach_hang_list = KhachHang.objects.filter(
        name__isnull=False,
        is_called=False,
        trang_thai=True,
    )
    grouped = defaultdict(list)
    for kh in khach_hang_list:
        grouped[kh.service].append(kh)
    return list(grouped.items())


# ============================================================
# Statistics & Feedback
# ============================================================

def get_feedback_statistics() -> dict:
    """
    Tính thống kê tỷ lệ đánh giá (hài lòng / không hài lòng).

    Returns:
        dict: {total, positive, negative, rate}
    """
    qs = KhachHang.objects.filter(feedback__isnull=False)
    total = qs.count()
    positive = qs.filter(feedback__gte=4).count()
    negative = total - positive
    rate = round((positive / total * 100), 1) if total else 0

    return {
        'total': total,
        'positive': positive,
        'negative': negative,
        'satisfaction_rate': rate,
    }


def get_feedback_chart_data() -> dict:
    """
    Dữ liệu chart phản hồi theo từng loại đánh giá.

    Returns:
        dict: {labels: [...], data: [...]}
    """
    from backend.customer.models import CapNhatDuLieu
    du_lieu = CapNhatDuLieu.objects.all()

    labels = []
    data = []
    for item in du_lieu:
        count = KhachHang.objects.filter(feedback_id=item.id).count()
        labels.append(item.name if hasattr(item, 'name') else str(item.id))
        data.append(count)

    return {'labels': labels, 'data': data}
