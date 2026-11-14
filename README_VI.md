# PIRB Studio 0.8.1

[English](README.md) · Chim bồ câu phản hồi bàn phím và chuột trên Windows.

## Cần gì để sử dụng?

| Thành phần | Yêu cầu |
| --- | --- |
| Hệ điều hành | Windows 10 từ bản 1809 trở lên hoặc Windows 11, **64-bit x64 Intel/AMD** |
| Dung lượng | Chừa **300 MB trống** cho ứng dụng và tệp tạm lúc cài |
| Màn hình | Phiên desktop Windows; khuyến nghị từ 1280 × 720 để dùng Settings thoải mái |
| Thiết bị | Bàn phím, chuột; loa/tai nghe chỉ cần nếu muốn có âm thanh |
| Phần mềm thêm | **Không cần Python, pip, WinRAR hay công cụ lập trình** |
| Internet | Chỉ cần lúc tải; ứng dụng dùng được ngoại tuyến |

Đã kèm Python 3.12.10, PySide6/Qt 6.8.3, ảnh, âm thanh, Settings Pythenians và hai ngôn ngữ. Setup dùng `tar.exe` có sẵn trên Windows tiêu chuẩn. Không hỗ trợ Windows 32-bit, native ARM64 hoặc chạy desktop thật trên macOS/Linux. 300 MB là khoảng dự phòng cài đặt, không phải RAM tối thiểu đã đo.

## Cài đặt

1. Vào **Releases**, tải **PIRB_Studio_0.8.1_Windows_x64_Setup.exe**. **Code → Download ZIP** chỉ là mã nguồn, không phải bộ cài.
2. Thoát hẳn PIRB bằng menu biểu tượng cạnh đồng hồ.
3. Mở Setup, đồng ý cài cho tài khoản hiện tại.
4. Mở **PIRB Studio** từ Desktop hoặc Start Menu.

Không cần quyền quản trị hay tệp cập nhật Settings riêng. Thư mục cài: `%LOCALAPPDATA%\Programs\PIRBStudio\0.8.1\PIRB`.

Bản portable: giải nén **toàn bộ** `PIRB_Studio_0.8.1_Windows_x64_Portable.zip`, mở `PIRB\PIRB.exe`, giữ `_internal` bên cạnh. Không mở trực tiếp trong WinRAR. Portable vẫn lưu tùy chọn vào hồ sơ Windows.

## Cách sử dụng

Nhấp phải PIRB hoặc biểu tượng cạnh đồng hồ → **Giao diện & âm thanh…**.

- **Ngôn ngữ / Language:** ở đầu Settings, chọn **Tiếng Việt / English**. Áp dụng ngay cho Settings và menu chuột phải, được lưu cho lần mở sau.
- **Vị trí & kích thước:** xoay cả cảnh −180° đến +180°, chiều rộng cơ sở 180–1200 px, bám góc hoặc chọn bố cục nhanh. **Canh bàn ngang** bù góc nghiêng của hình bàn.
- **Giao diện:** chọn nền/nhập ảnh PNG/JPG/WEBP dưới 30 MB; xoay/phóng/dịch/chỉnh sáng ảnh; chỉnh tư thế, biểu cảm, RGB và hiệu ứng.
- **Âm thanh:** Thock/Clicky/Tactile; bật tiếng phím, chuột, gù; chỉnh âm lượng riêng và nghe thử.
- **Ctrl + cuộn:** thu/phóng; **Alt + cuộn:** xoay; giữ chuột trái kéo để di chuyển cả cảnh.
- Menu có tạm dừng, khóa vị trí, bấm xuyên, hiện/ẩn và thoát. Nếu đã bật bấm xuyên, mở Settings qua biểu tượng cạnh đồng hồ.

Mọi thay đổi lưu tự động. Chỉ chạy một phiên PIRB. Không tự khởi động cùng Windows; nếu muốn, chép shortcut Desktop vào thư mục mở bằng **Win + R → `shell:startup`**.

## Nâng cấp, gỡ và xử lý lỗi

Thoát bản cũ trước khi cài. 0.8.1 đọc lại tùy chọn cũ; ngôn ngữ mặc định là tiếng Việt khi chưa có lựa chọn. Setup không xóa thư mục bản cũ hoặc dọn Downloads.

Gỡ bản cài qua **Windows Settings → Apps → PIRB Studio 0.8.1 → Uninstall** hoặc `Uninstall.exe` trong thư mục cài. Tùy chọn và ảnh riêng vẫn giữ lại. Với portable: thoát rồi xóa thư mục giải nén; trình gỡ đi kèm chỉ dành cho đường dẫn của bản cài.

Không mở được: chạy `_internal\support\DIAGNOSTICS.bat`, kiểm tra `%LOCALAPPDATA%\PIRBDesktop\startup-error.log` nếu có. Không có tiếng: kiểm tra thiết bị phát/Volume Mixer và tab Âm thanh. Không nhận phím từ app khác: thử một app mở bình thường, không nâng quyền. PIRB báo đã chạy: tìm biểu tượng ở khay hệ thống, có thể trong mũi tên cạnh đồng hồ.

Bộ cài chưa ký số nên có thể hiện cảnh báo nhà phát hành; ứng dụng không yêu cầu tắt bảo vệ. Khi báo lỗi, gửi nguyên thông báo, phiên bản Windows và PIRB.

Ứng dụng giữ trạng thái phím tạm thời trong bộ nhớ, không ghi nội dung gõ, không gửi ảnh/phím qua mạng. Tùy chọn dùng `QSettings('PIRBCompanion', 'Desktop')`, thường ở `HKEY_CURRENT_USER\Software\PIRBCompanion\Desktop`; ảnh riêng được chép vào vùng dữ liệu người dùng của `PIRBCommunity/PIRBDesktop`.

## Phiên bản và mã nguồn

[CHANGELOG](CHANGELOG.md) · [Hướng dẫn chạy code/build](README.md#develop-and-build) · [Tình trạng kiểm chứng](docs/VALIDATION.md)

Chạy từ code cần Python 3.12 x64 và `requirements.txt`; dùng bộ cài thì không cần. Đây là dự án cộng đồng, không phải sản phẩm Pyth chính thức. Chưa chọn giấy phép nguồn mở cho code gốc; xem [LICENSE](LICENSE), [thành phần bên thứ ba](THIRD_PARTY_NOTICES.md) và [nguồn ảnh/âm thanh](app/ASSET_CREDITS.md).
