# Customer Presence Detection Experiment

Thu muc nay dung de test rieng bai toan: camera co nhan dien duoc khach hang dang su dung may kiosk hay khong.

No khong duoc import vao Django runtime hien tai. Du lieu raw se nam trong `data/` va duoc ignore boi git.

## Muc tieu v1

Khong train model moi. Muc tieu la thu mot bo video nho, co nhan va metadata, de phan tich model hien co co hoat dong on trong dieu kien kiosk that hay khong.

Phan loai tung doan video/ngan canh theo cac nhan tham chieu:

- `using_machine`: co khach dang dung/truoc kiosk va co y dinh thao tac.
- `not_using_machine`: co nguoi di ngang, dung xa, hoac khong thao tac kiosk.
- `empty`: khong co nguoi trong vung kiosk.
- `ambiguous`: kho gan nhan, dung de review lai.

## Chay quay video nguoi di qua di lai

```powershell
.\.venv\Scripts\python.exe experiments\customer_presence_detection\collect_presence_dataset.py --camera-index 0
```

Neu dang dung PowerShell ngay trong thu muc `experiments\customer_presence_detection`, chay:

```powershell
..\..\.venv\Scripts\python.exe .\collect_presence_dataset.py --camera-index 0
```

Script se mo camera va quay 1 source:

- `PASSING_BY`: 10 giay nguoi di qua di lai, khong dung lai su dung kiosk.

Phim tat khi cua so camera dang mo:

- `Enter`: bat dau quay.
- `q`: thoat.

Script tao:

- `data/videos/passing_by/<session_id>_passing_by.mp4`
- `data/metadata/sessions.jsonl`
- `data/metadata/segments.jsonl`
- `data/metadata/events.csv`

## Viec can lam khi quay

1. Dat camera dung goc thu nghiem va khong doi goc trong luc quay.
2. Chay script, doi cua so camera hien preview.
3. Dung o cua hoac ngoai khung hinh.
4. Bam `Enter`.
5. Trong 10 giay, di qua lai trong khung hinh nhu nguoi di ngang phong.
6. Khong dung lai truoc kiosk, khong nhin/cham man hinh kiosk.
7. Script tu dung sau 10 giay.

## Khuyen nghi thu thap phan tich

Vi da co model, giai doan nay chi can 12-24 video ngan, moi video 30-90 giay, tap trung vao cac truong hop model de sai.

Ke hoach chi tiet nam o `DATA_COLLECTION_PLAN.md`.
