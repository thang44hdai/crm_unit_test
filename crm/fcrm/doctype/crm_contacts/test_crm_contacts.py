import frappe
import unittest
from frappe.exceptions import DoesNotExistError, ValidationError
from your_app.api.contact import (
    get_contact, get_linked_deals,
    create_new, set_as_primary,
    search_emails
)

class TestContactFunctions(unittest.TestCase):

    def setUp(self):
        # Tạo một contact test trước mỗi test case
        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Test",
            "last_name": "User"
        })

        # Thêm email vào contact với trường là email chính
        self.contact.append("email_ids", {
            "email_id": "test@example.com",
            "is_primary": 1,
            "parenttype": "Contact",
            "parentfield": "email_ids"
        })

        # Thêm số điện thoại vào contact với trường là số chính
        self.contact.append("phone_nos", {
            "phone": "0123456789",
            "is_primary_mobile_no": 1,
            "parenttype": "Contact",
            "parentfield": "phone_nos"
        })

        # Lưu contact vào database
        self.contact.insert()

    def tearDown(self):
        # Xóa contact test sau mỗi test case để làm sạch dữ liệu
        frappe.delete_doc("Contact", self.contact.name, force=True)

    def test_get_contact_success(self):
        # Kiểm tra lấy contact thành công
        result = get_contact(self.contact.name)
        self.assertEqual(result["name"], self.contact.name)
        self.assertGreaterEqual(len(result["email_ids"]), 1)
        self.assertGreaterEqual(len(result["phone_nos"]), 1)

    def test_get_contact_not_found(self):
        # Kiểm tra lỗi khi contact không tồn tại
        with self.assertRaises(DoesNotExistError):
            get_contact("non-existent")

    def test_create_new_email(self):
        # Kiểm tra thêm email mới cho contact
        result = create_new(self.contact.name, "email", "new@example.com")
        self.assertTrue(result)

    def test_create_new_phone(self):
        # Kiểm tra thêm số điện thoại mới cho contact
        result = create_new(self.contact.name, "mobile_no", "0987654321")
        self.assertTrue(result)

    def test_create_new_invalid_field(self):
        # Kiểm tra lỗi khi thêm dữ liệu với field không hợp lệ
        with self.assertRaises(ValidationError):
            create_new(self.contact.name, "invalid_field", "value")

    def test_set_as_primary_email(self):
        # Kiểm tra gán email làm email chính
        create_new(self.contact.name, "email", "first@example.com")
        create_new(self.contact.name, "email", "second@example.com")
        set_as_primary(self.contact.name, "email", "second@example.com")

        contact = frappe.get_doc("Contact", self.contact.name)
        primaries = [e for e in contact.email_ids if e.is_primary]
        self.assertEqual(len(primaries), 1)
        self.assertEqual(primaries[0].email_id, "second@example.com")

    def test_set_as_primary_invalid_field(self):
        # Kiểm tra lỗi khi gán primary với field không hợp lệ
        with self.assertRaises(ValidationError):
            set_as_primary(self.contact.name, "invalid", "value")

    def test_search_emails(self):
        # Kiểm tra tìm kiếm email theo từ khóa
        create_new(self.contact.name, "email", "findme@example.com")
        result = search_emails("findme")
        found = any("findme@example.com" in r for r in result)
        self.assertTrue(found)

    def test_get_linked_deals_no_deals(self):
        # Kiểm tra khi contact không liên kết với CRM Deal nào
        result = get_linked_deals(self.contact.name)
        self.assertEqual(result, [])
