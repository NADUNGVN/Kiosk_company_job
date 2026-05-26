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

## Chay quay 2 video dau tien

```powershell
.\.venv\Scripts\python.exe experiments\customer_presence_detection\collect_presence_dataset.py `
  --camera-index 0 `
  --output-dir experiments\customer_presence_detection\data
```

Script se mo camera va quay 2 source:

- `NO_PERSON`: 10 giay phong trong.
- `PERSON`: 30 giay co nguoi di tu cua vao gan kiosk.

Phim tat khi cua so camera dang mo:

- `Enter`: bat dau phase hien tai.
- `q`: thoat.

Script tao:

- `data/videos/no_person/<session_id>_no_person.mp4`
- `data/videos/person/<session_id>_person.mp4`
- `data/metadata/sessions.jsonl`
- `data/metadata/segments.jsonl`
- `data/metadata/events.csv`

## Viec can lam khi quay

1. Dat camera dung goc thu nghiem va khong doi goc trong luc quay.
2. Chay script, doi cua so camera hien preview.
3. Ra khoi khung hinh, de phong trong.
4. Bam `Enter` de quay `NO_PERSON` trong 10 giay.
5. Sau khi script doi phase `PERSON`, dung o cua hoac ngoai khung hinh.
6. Bam `Enter`, sau do di tu cua vao gan kiosk ben phai anh.
7. Trong 30 giay, dung truoc kiosk, nhin vao man hinh/camera 2-3 giay, co the gio tay hoac cham man hinh.
8. Khong can bam them; script tu dung sau 30 giay.

## Khuyen nghi thu thap phan tich

Vi da co model, giai doan nay chi can 12-24 video ngan, moi video 30-90 giay, tap trung vao cac truong hop model de sai.

Ke hoach chi tiet nam o `DATA_COLLECTION_PLAN.md`.
