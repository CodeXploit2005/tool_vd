# Chạy MoonReel trên máy này

Mở `Mo MoonReel.cmd`. File này gọi `Start-MoonReel.ps1` để:

1. Bật PostgreSQL 18 trực tiếp trên Windows và kiểm tra kết nối.
2. Bật container Muse2API trong Docker.
3. Chạy giao diện production và worker, rồi mở http://localhost:3000/.

Database dùng `127.0.0.1:5435`, chỉ lắng nghe trên máy này. Dữ liệu nằm ở
`moonreel-data/postgres-windows`. Không xóa thư mục này.

Giao diện dùng `next start`, không cần biên dịch lại mỗi lần chuyển trang.
Sau khi thay đổi mã nguồn, dừng web trước rồi chạy
`pwsh -NoProfile -File .\Start-MoonReel.ps1 -Rebuild` để tạo bản production mới.

## Kiểm tra database

Trong thư mục `moonreel/moonreel-studio`, chạy:

```powershell
node --env-file=.env scripts/check-database.mjs
```

## Bản sao trước khi chuyển database

- Dump PostgreSQL: `moonreel-data/backups/moonreel-before-windows.dump`.
- Cấu hình cũ: `moonreel/moonreel-studio/.env.docker-backup`.
- Container PostgreSQL cũ: `moonreel-postgres`, đã dừng, chưa xóa volume.

Đã đối chiếu số bản ghi và checksum của cả 8 bảng dữ liệu trước khi dừng
database Docker. Dữ liệu phát sinh sau khi chuyển nằm trong database Windows.
Muốn quay lại Docker cần chuyển cả dữ liệu mới, không chỉ chép lại `.env` cũ.

Muse2API vẫn sử dụng Docker. Khi trạng thái Muse báo mất kết nối nhưng các
trang vẫn mở được, kiểm tra Muse riêng; database Windows không phụ thuộc Docker.
