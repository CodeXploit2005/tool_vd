# Phần đã đưa lên và phần giữ ở máy

## Được đưa lên

- Toàn bộ source hiện tại của Studio: trang, component, CSS, i18n, API, schema, provider, pipeline FFmpeg, worker, script nhập prompt và nhiều ảnh sản phẩm.
- Logo KeyZone, font render, font preview, tài nguyên public và giấy phép liên quan.
- Source backend Python hiện tại, gồm `login_bridge.py`, trang quản trị, extension tùy chọn, tools, deploy và tests.
- README upstream, tài liệu kiến trúc, demo upstream và giấy phép gốc của cả hai dự án.
- Launcher Windows cùng tài liệu chạy local hiện có.
- Dockerfile và Blueprint Render mới, baseline SQL, bootstrap, supervisor, lớp đăng nhập Studio cho public deployment, test và hướng dẫn triển khai.

`docs/SOURCE-INVENTORY.json` liệt kê từng file lấy từ máy cùng SHA-256 tại thời điểm đóng gói. Các điều chỉnh phục vụ cloud nằm trong commit: proxy đăng nhập, `/api/ready`, origin HTTPS trong muse-connect và COPY `login_bridge.py` vào Docker backend. Không bỏ phần nào của giao diện hiện tại.

## Không đưa lên, lý do cụ thể

| Đường dẫn / nhóm | Lý do |
| --- | --- |
| `.env`, `.env.docker-backup`, key/token/cookie thật | Là thông tin truy cập; thay bằng `.env.example` và biến môi trường Render |
| `moonreel-data/`, `muse2api-local/data/`, browser profiles | Database, phiên đăng nhập, tài khoản, media người dùng và backup; không cần để build source |
| `node_modules/`, `.venv/`, `.next/`, `__pycache__/`, `*.tsbuildinfo` | Thư viện/cache/output sinh tự động; cài lại từ package.json, pnpm-lock.yaml, requirements.txt |
| `*.log`, `*.pid`, `wsl-repair.log` | Trạng thái máy cục bộ; không dùng để triển khai |
| `ui-checks/`, `connect-probe.jpg`, `desktop-video-fixed.png` | Ảnh kiểm thử/debug, có thể chứa thông tin phiên hoặc nội dung người dùng |
| `ui-preview/`, `UI-REDESIGN-HANDOFF/` | Prototype và bản sao source/UI cũ để bàn giao thiết kế, không phải code giao diện đang chạy; bản gốc vẫn còn trên máy |
| `.git/` của hai repo upstream | Không lồng lịch sử repo khác vào repo mới; vẫn giữ LICENSE và ghi nguồn gốc |
| `docker-compose.override.yml` cục bộ | Override riêng máy Windows; repo mới có Docker Compose ở gốc dùng backend hiện tại |

Các file này không bị xóa ở máy. Toàn bộ việc đóng gói được làm trong checkout riêng `.publish/tool_vd` để không đổi remote upstream hoặc ảnh hưởng ứng dụng đang chạy.
