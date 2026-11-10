# Kiểm tra trước khi đưa lên GitHub

Ngày chuẩn bị: 2026-11-11.

## Đã qua

- Cài riêng 416 package từ `pnpm-lock.yaml` bằng `pnpm install --offline --frozen-lockfile`; không đưa node_modules vào Git.
- Production build Next.js hoàn tất với biến môi trường placeholder, không dùng `.env` cá nhân.
- TypeScript `tsc --noEmit` và ESLint cho phần bảo vệ public deployment/API mới.
- 17 kiểm thử Node: import/parse script, lập storyboard, ảnh sản phẩm nhiều góc, ghép reference sheet, file streaming/cancel và đăng nhập Studio.
- 8 kiểm thử Python cho vòng đời phiên kết nối Muse, không đăng nhập hoặc ghi tài khoản thật.
- `render.yaml` hợp lệ theo JSON schema chính thức tại `https://render.com/schema/render.yaml.json`.
- `docker compose config --quiet` hợp lệ với giá trị placeholder; cú pháp supervisor/bootstrap được `node --check` kiểm tra.
- Database PostgreSQL thử riêng: tạo toàn bộ schema, seed 4 ngách mẫu, chạy bootstrap hai lần vẫn giữ nguyên dữ liệu.
- Chạy production web riêng với cấu hình bind 0.0.0.0: `/api/ready` trả 200; tài khoản/API/media trả 401 khi chưa đăng nhập; trang chính trả 200 sau đăng nhập. Database thử đã được xóa, không dùng database đang làm việc.
- Rà soát source để tìm giá trị key/token thật đang dùng trên máy và mẫu GitHub token/private key: không tìm thấy trong bản xuất.

## Chưa kiểm thử

- Chưa build/chạy image Docker: Docker CLI có mặt nhưng Docker engine của máy không chạy.
- Chưa tạo dịch vụ hoặc triển khai thật trên tài khoản Render. Chưa phát sinh việc mua service/disk từ thao tác này.
- Chưa thử tài khoản Muse, tạo ảnh/video hay kết nối Chromium từ IP Render. Việc Muse chấp nhận tài khoản/vùng/IP và chất lượng clip cần kiểm tra sau khi triển khai.
- GitHub Actions đã có workflow, nhưng kết quả lần chạy đầu phụ thuộc runner sau khi push; báo cáo này không khẳng định CI đã chạy thành công trên GitHub.

Kiểm thử triển khai local (cần PostgreSQL local và quyền tạo database thử):

```sh
# Trong root repo; DATABASE_URL trỏ tới PostgreSQL local.
node deploy/tests/verify-deploy.mjs
```

Test chỉ tạo/xóa database có tên `codex_publish_probe_<random>`. Baseline schema và script seed không reset database hiện có.
