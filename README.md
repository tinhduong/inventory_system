# Inventory Management System (Django)

Hệ thống quản lý kho, sản phẩm, đơn hàng và công nợ được xây dựng bằng Django 5.x.

## Chức năng chính
- Quản lý Kho (Warehouse) & Tồn kho (Stock).
- Quản lý Sản phẩm (Product).
- Quản lý Đơn bán hàng (Sales Order) & Đơn nhập hàng (Purchase Order).
- Tự động trừ/cộng tồn kho khi xác nhận đơn hàng.
- Quản lý Công nợ (Debt) khách hàng và nhà cung cấp.
- Trang xem đơn hàng công khai cho khách hàng (Public Order View).
- Phân quyền: Admin (Toàn quyền), Employee (Nhân viên vận hành).

## Cài đặt & Chạy thử

1. **Cài đặt môi trường**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install django
   ```

2. **Migrate Database**:
   ```bash
   python manage.py migrate
   ```

3. **Seed dữ liệu mẫu**:
   ```bash
   python manage.py seed_demo_data
   ```
   *Tài khoản mẫu:*
   - Admin: `admin` / `admin123`
   - Employee: `emp` / `emp123`

4. **Chạy server**:
   ```bash
   python manage.py runserver
   ```
   Truy cập: `http://127.0.0.1:8000/`

## Cấu trúc project
- `accounts/`: User, Customer, Auth.
- `catalog/`: Kho, Sản phẩm, Tồn kho.
- `orders/`: Đơn hàng và logic xử lý kho.
- `debt/`: Công nợ và thanh toán.
- `inventory_system/`: Cài đặt project.
- `templates/`: Giao diện (Bootstrap 5).

## Lưu ý kỹ thuật
- Sử dụng **Django Services** để xử lý logic nghiệp vụ phức tạp (confirm order).
- **Transaction Atomic** đảm bảo tính toàn vẹn dữ liệu khi cập nhật kho và công nợ.
- **UUID tokens** cho phép xem đơn hàng không cần đăng nhập.
