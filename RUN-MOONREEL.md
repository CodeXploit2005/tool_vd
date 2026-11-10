# MoonReel tren Windows, khong can Docker

## Dán kịch bản / prompt có sẵn

Trong **Tạo video → Dán prompt có sẵn**, dán `Cảnh 1:`, `Cảnh 2:` (hoặc `Scene 1:`),
hay JSON `{ "title": "Tên video", "scenes": [{ "visualPrompt": "Prompt cảnh", "narration": "Lời dẫn tùy chọn", "camera": "Chuyển động tùy chọn" }] }`.
Kiểm tra các cảnh và đánh dấu xác nhận trước khi nhập. Số cảnh được suy ra từ nội dung;
mỗi cảnh là một clip khoảng 10 giây. Ngách chỉ sắp xếp dự án; mặc định giọng đọc, phong cách
và số cảnh của ngách không áp dụng. Nhập kịch bản chỉ lưu bản nháp để duyệt, chưa gọi AI hay tạo media.
Prompt nhập sẵn không tự viết lại khi Muse từ chối; hãy sửa cảnh rồi thử lại.

Máy mới có database cũ cần chạy một lần tại `moonreel/moonreel-studio`:
`node --env-file=.env scripts/add-script-import.mjs`.

## Khởi động

Nhan dup `MoonReel.cmd`, hoac mo PowerShell tai thu muc nay va chay:

```powershell
.\Start-MoonReel.ps1
```

Lenh nay bat PostgreSQL, Muse2API Python, web va worker, roi mo http://localhost:3000/.
Trang quan tri Muse2API: http://localhost:18610/admin.
Trong tien ich trinh duyet, giu dia chi http://localhost:18610 va API key hien tai.

Sau khi sua code ung dung:

```powershell
.\Start-MoonReel.ps1 -Rebuild
```

Neu dang dung `pnpm dev`, giu terminal do mo va chay lenh khoi dong trong terminal khac.
Script se dung lai web dang chay. Dung web truoc khi chay `-Rebuild`.

## Chay rieng Muse2API

```powershell
.\Start-Muse2API.ps1
```

## Cau hinh da chuyen

- Python rieng: `muse2api-local\.venv`.
- Cau hinh rieng: `muse2api-local\.env`, dung cung MUSE2API_KEY voi studio.
- Du lieu cu: `moonreel-data\muse2api`, duoc tro boi MUSE2API_DATA_DIR.
- Chrome profile rieng: `moonreel-data\muse2api-profiles`.
- Log Muse2API: `muse2api-local\muse.log` va `muse-error.log`.
- PostgreSQL van dung cluster Windows `moonreel-data\postgres-windows`.

Docker khong con duoc goi boi script khoi dong. Khong chay container Muse2API dong thoi voi ban Python vi hai ban dung cung cong va du lieu.

Neu can cai lai thu vien Python:

```powershell
cd muse2api-local
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Giu lai file .env rieng; khong chia se API key hoac cookie.

## Anh san pham cho video marketing

- Trong ca "Nhap y tuong" va "Dan prompt co san", bam icon kep giay trong khung nhap de them toi da 6 anh san pham. Anh duoc giu khi doi tab, luu vao du an va dung lam tham chieu cho tung keyframe; clip dung keyframe do lam khung dau.
- Ho tro JPG, JPEG, PNG, WebP toi da 25 MB moi anh. Cac anh duoc luu rieng va ghep thanh bang tham chieu khi gui Muse; khong chi dung anh dau tien. AI duoc yeu cau giu kieu dang, mau, bao bi va nhan san pham; do chinh xac cuoi cung phu thuoc dich vu tao anh/video.
- Khi trien khai vao database khac, chay trong moonreel/moonreel-studio: `node --env-file=.env scripts/add-product-reference.mjs`. Cot moi giu nguyen y nghia anh phong canh cua cac du an cu.
- Khoi dong lai worker khi hang doi da ranh de nap thay doi pipeline.
