# Triển khai KeyZone lên Render.com

## Các tài nguyên được chuẩn bị

`render.yaml` tạo ba tài nguyên cùng vùng Singapore:

1. `keyzone-studio`: Docker web service, chạy Next.js và worker trong cùng container. Ổ `/var/data/studio` lưu ảnh sản phẩm, keyframe, clip, video cuối và ngách riêng.
2. `keyzone-muse`: Docker private service, chạy Python + Chromium, lưu phiên Muse và media backend ở `/var/data/muse`.
3. `keyzone-db`: PostgreSQL dùng connection string nội bộ. Không mở kết nối database ra Internet trong Blueprint.

Web và worker phải dùng cùng storage. Render không cho nhiều service cùng gắn một persistent disk, nên bản này ghép web và worker dưới một supervisor. Nếu muốn tách riêng hoặc tăng nhiều instance, cần chuyển storage sang S3/R2 và sửa pipeline trước.

**Blueprint này sử dụng dịch vụ và ổ đĩa trả phí**, không phải bộ cấu hình free tier. Hai service chọn `standard`, database chọn `basic-256mb`; kiểm tra mức giá đang hiện trong Dashboard trước khi tạo. Có thể cần tăng RAM/CPU khi ghép video dài. Auto-deploy được tắt để tránh ngắt render đang chạy.

## Các bước trên Dashboard

1. Kết nối GitHub với Render, cấp quyền repo `CodeXploit2005/tool_vd`.
2. New → Blueprint, chọn repo và nhánh `main`, dùng `render.yaml` ở gốc.
3. Đặt `STUDIO_ACCESS_PASSWORD` dài, riêng biệt; username mặc định là `admin`. Đây là tài khoản vào Studio, không phải tài khoản Muse.
4. Xem lại các gói trả phí rồi tạo tài nguyên. `MUSE2API_KEY` được sinh ngẫu nhiên cho private service và tham chiếu sang Studio; không cần chép key vào Git.
5. Chờ hai service sẵn sàng. Mở URL HTTPS của `keyzone-studio`, nhập username/password Studio.
6. Vào Tài khoản → Kết nối Muse. Đăng nhập theo hướng dẫn, duyệt cảnh rồi thử một clip ngắn trước khi chạy dự án dài.

Studio nhận `MUSE2API_INTERNAL_HOSTPORT` từ Blueprint; entrypoint đổi thành URL HTTP nội bộ lúc chạy. Backend không có URL public. `/api/ready` kiểm tra database để Render theo dõi web; `/api/health` hiển thị trạng thái Muse trong ứng dụng sau đăng nhập. Backend chưa có tài khoản Muse không làm web bị đánh dấu hỏng.

## Database và cập nhật

Lần khởi động đầu, `deploy/bootstrap.mjs` tạo schema từ `deploy/initial-schema.sql` nếu database hoàn toàn mới, rồi seed ngách mẫu. Những lần sau không xóa hoặc reset dữ liệu. Các cột import prompt và nhiều ảnh sản phẩm được bổ sung bằng `ADD COLUMN IF NOT EXISTS`.

`moonreel/moonreel-studio/drizzle/` giữ baseline do Drizzle sinh. Với thay đổi schema tương lai, tạo migration có kiểm tra và cập nhật bootstrap; không dùng `db:push --force` trên database có dữ liệu. Sao lưu database và disk trước các thay đổi lớn.

Không tự động đưa dữ liệu Windows hiện tại lên cloud. Muốn mang dự án cũ sang, chuyển PostgreSQL, storage và dữ liệu Muse qua kênh riêng. File JSON tài khoản, cookie và profile trình duyệt không được commit vào Git.

## Cấu hình tùy chọn

Trong service `keyzone-studio`, có thể thêm các biến dưới đây trong Dashboard để dùng AI Gateway hoặc voice-over. Bỏ hẳn biến URL tùy chọn nếu không dùng; đừng nhập chuỗi rỗng vào biến yêu cầu URL.

- `CF_AIG_BASE_URL` hoặc `CF_AIG_ACCOUNT_ID`, `CF_AIG_GATEWAY_ID`
- `CF_AIG_TOKEN` hoặc `CF_AIG_PROVIDER_KEY`, `CF_AIG_BYOK_ALIAS`
- `SCRIPT_MODEL` (mặc định `deepseek/deepseek-chat`)
- `ELEVENLABS_API_KEY`, `ELEVENLABS_MODEL`

Các biến thực tế chỉ nhập trong Render, không sửa `.env.example` thành khóa thật. `STORAGE_DIR` và `NICHES_DIR` đã trỏ vào ổ bền vững. `MUSE_CONCURRENCY=1` hạn chế tải Chromium.

## Giới hạn đã biết

- Đây là Studio cá nhân/nhóm tin cậy với một lớp đăng nhập chung; chưa có phân quyền và dữ liệu riêng cho từng khách.
- Persistent disk giữ file qua restart nhưng làm deploy phải tạm dừng instance cũ. Dừng gửi job mới và đợi render xong trước khi Manual Deploy.
- Muse có thể yêu cầu OTP, từ chối prompt, chặn vùng hoặc giới hạn tài khoản. Hạ tầng Render không bảo đảm Muse sẽ chấp nhận IP datacenter; thử trên tài khoản của bạn trước khi chạy quy mô lớn.
- Máy chuẩn bị mã chưa có Docker engine đang chạy; cấu hình Docker chưa được build/chạy tại đây và chưa tạo tài nguyên Render thật. Xem VALIDATION.md.

Tài liệu chính thức đã đối chiếu: [Blueprint](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [private network](https://render.com/docs/private-network), [Docker](https://render.com/docs/docker).
