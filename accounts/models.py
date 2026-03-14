from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ADMIN = 'ADMIN'
    EMPLOYEE = 'EMPLOYEE'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (EMPLOYEE, 'Nhân viên'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=EMPLOYEE)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Customer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên đối tác")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    address = models.TextField(blank=True, null=True, verbose_name="Địa chỉ")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Đối tác"
        verbose_name_plural = "Đối tác"
