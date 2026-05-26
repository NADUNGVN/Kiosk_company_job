# Ke Hoach Thu Thap Video Phan Tich Model Nhan Dien Khach Dang Su Dung Kiosk

## Dinh nghia bai toan

Muc tieu khong phai train model moi va khong nhan dien danh tinh khach hang. Muc tieu hien tai la thu mot bo video nho de phan tich model da co: model co phat hien dung trang thai "co khach dang su dung may" trong dieu kien kiosk that hay khong.

Nen thu du lieu theo hanh vi va boi canh:

- Khach dung gan kiosk, quay mat/than ve man hinh, cham man hinh hoac dang doc noi dung.
- Khach dung truoc kiosk nhung chua cham man hinh.
- Nguoi di ngang qua camera, dung xa, nhan vien dung canh.
- Khong co nguoi.

V1 giu 4 nhan trong README de lam ground truth tham chieu khi xem lai ket qua model.

## Loai video can co

Thu bang dung camera va vi tri gan tren kiosk, khong dung video internet. Moi video nen dai 30-90 giay, goc quay va do phan giai giong thuc te.

Can co cac nhom:

- `using_machine`: 1 nguoi thao tac binh thuong, doc man hinh, cham man hinh, quet CCCD/QR neu co.
- `using_machine_multi_person`: 2 nguoi cung dung truoc may, 1 nguoi thao tac, 1 nguoi dung canh.
- `not_using_machine`: nguoi di ngang, dung doi tu xa, nhan vien di qua, nguoi nhin sang nhung khong thao tac.
- `empty`: khong co nguoi, chi co nen phong, anh sang thay doi.
- `occlusion`: nguoi bi che mot phan, cui xuong, quay lung, cam vat dung.
- `lighting`: sang manh, toi, nguoc sang, den phong nhap nhay, anh sang ngoai troi neu kiosk gan cua.
- `camera_noise`: rung nhe, blur, camera bi lech goc, vat the che camera mot phan.

## So luong khuyen nghi

Vi da co model, khong can 100+ video. Dot phan tich dau tien nen thu it nhung co chu dich:

- 4-6 video `using_machine`, moi video 30-90 giay.
- 3-5 video `not_using_machine`, moi video 30-90 giay.
- 2-4 video `empty`, moi video 30-90 giay.
- 3-6 video edge cases/`ambiguous`, moi video 30-90 giay.
- Tong: khoang 12-24 video, tu 10 den 30 phut footage.

Neu model cho ket qua on, co the dung lai o muc nay. Chi tang them video khi gap loi:

- False positive: model bao co khach dang dung may khi chi co nguoi di ngang/dung doi.
- False negative: khach dang thao tac nhung model bao khong co.
- Cham tre: model can qua lau moi doi trang thai.
- Khong on dinh: trang thai nhay lien tuc khi khach dung yen.

## Kich ban quay tai kiosk

Moi kich ban nen quay 1-2 lan truoc, uu tien dung dung camera/goc lap thuc te:

1. Khach buoc vao, dung truoc may, thao tac man hinh 30-60 giay, roi roi di.
2. Khach dung gan may nhung khong cham man hinh, doc noi dung, roi di.
3. Nguoi di ngang qua phia truoc camera, khong dung lai.
4. Nguoi dung doi cach kiosk 1-2 met.
5. Nhan vien dung canh kiosk ho tro khach.
6. Hai nguoi dung truoc may, mot nguoi thao tac.
7. Khach thap/cao, dung lech trai/phai, cuoi xuong.
8. Khach cam tui, non bao hiem, khau trang, ao khoac.
9. Khong co nguoi, phong sang/toi, man hinh kiosk thay doi.
10. Truong hop kho: nguoi dung sat camera nhung khong thao tac, tre em, nguoi quay lung.

Bo video toi thieu nen co:

- 2 video khach thao tac ro rang.
- 2 video khach dung/doc man hinh nhung chua cham.
- 2 video nguoi di ngang.
- 2 video nguoi dung doi xa kiosk.
- 2 video empty.
- 2 video edge case: nhieu nguoi, che mot phan, anh sang xau.

## Quy tac gan nhan

- Gan nhan theo doan video de lam ground truth tham chieu cho viec xem lai ket qua model.
- Neu trong doan co ca nguoi di ngang va khach su dung may, cat thanh cac segment rieng.
- Neu khong chac, gan `ambiguous` va ghi note.
- Khong dua mat/ten/CCCD vao metadata. Dung `participant_id` vo danh nhu `pilot_001`.

## Dau ra mong doi sau dot phan tich

- Bang tong hop moi video: ground truth, model output, dung/sai, thoi gian delay, ghi chu loi.
- Danh sach tinh huong model hay sai.
- Quyet dinh tiep theo: chinh nguong, chinh ROI camera, them logic thoi gian lien tuc, hay moi can thu them video.
