# 📐 KML Polygon Renamer & Exporter

Ứng dụng Desktop GUI thương mại hỗ trợ đổi tên hàng loạt polygon (`Untitled Polygon`) trong file KML từ Google Earth và xuất thành các file KML riêng lẻ (Outline-only).

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![GUI](https://img.shields.io/badge/GUI-Tkinter-green.svg)

---

## 🌟 Tính năng chính

- 📁 **Đổi tên hàng loạt**: Đổi tên tự động các polygon `Untitled Polygon` theo định dạng `PREFIX1`, `PREFIX2`, ...
- ⚙️ **Nhận diện Folder tự động**: Tự đọc danh sách `<Folder>` trong KML và đề xuất Prefix theo tên thư mục (ví dụ: `ABCD` → `ABCD_Ca`).
- 📤 **Xuất file KML riêng lẻ (Outline)**: Mỗi polygon có thể được xuất thành 1 file KML riêng biệt chỉ có nét vẽ (đỏ, độ dày 2px), không tô màu bên trong.
- 🎨 **Giao diện thương mại (Light Theme)**:
  - Sidebar quy trình từng bước.
  - Form nhập liệu gọn gàng không cần cuộn trang.
  - Nhật ký hoạt động chi tiết có mã màu (Realtime Log).
  - Thanh tiến trình xử lý.

---

## 🚀 Hướng dẫn cài đặt & Sử dụng

### Cách 1: Chạy từ mã nguồn Python

```bash
# Cài đặt thư viện (nếu đóng gói)
pip install pyinstaller

# Chạy ứng dụng
python kml_renamer.py
```

### Cách 2: Đóng gói thành file `.exe`

```bash
pyinstaller --onefile --noconsole --name "KML_Polygon_Tool" kml_renamer.py
```
File `.exe` sẽ được tạo trong thư mục `dist/KML_Polygon_Tool.exe`.
