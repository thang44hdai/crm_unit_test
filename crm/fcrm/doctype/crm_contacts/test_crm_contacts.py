import frappe
import unittest
from frappe.exceptions import DoesNotExistError, ValidationError, PermissionError
from crm.api.contact import (
    get_contact, get_linked_deals,
    create_new, set_as_primary,
    search_emails, update_deals_email_mobile_no
)

class TestContactFunctions(unittest.TestCase):

    def setUp(self):
        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Test",
            "last_name": "User"
        })

        self.contact.append("email_ids", {
            "email_id": "test@example.com",
            "is_primary": 1
        })

        self.contact.append("phone_nos", {
            "phone": "0123456789",
            "is_primary_mobile_no": 1
        })

        self.contact.insert()

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.delete_doc("Contact", self.contact.name, force=True)

    # Nhiệm vụ: Lấy thông tin contact hợp lệ
    def test_get_contact_success(self):
        result = get_contact(self.contact.name)
        self.assertEqual(result["name"], self.contact.name)
        self.assertTrue(len(result["email_ids"]) >= 1)
        self.assertTrue(len(result["phone_nos"]) >= 1)

    # Nhiệm vụ: Kiểm tra khi contact không tồn tại
    def test_get_contact_not_found(self):
        with self.assertRaises(DoesNotExistError):
            get_contact("non-existent")

    # Nhiệm vụ: Tạo email mới cho contact
    def test_create_01(self):
        result = create_new(self.contact.name, "email", "new@example.com")
        self.assertTrue(result)

    # Nhiệm vụ: Tạo số điện thoại mới cho contact
    def test_create_02(self):
        result = create_new(self.contact.name, "mobile_no", "0988888888")
        self.assertTrue(result)

    # Nhiệm vụ: Thử tạo trường không hợp lệ
    def test_create_03(self):
        with self.assertRaises(ValidationError):
            create_new(self.contact.name, "invalid_field", "value")

    # Nhiệm vụ: Đặt email cụ thể làm primary
    def test_set_as_primary_01(self):
        create_new(self.contact.name, "email", "a@example.com")
        create_new(self.contact.name, "email", "b@example.com")
        set_as_primary(self.contact.name, "email", "b@example.com")
        contact = frappe.get_doc("Contact", self.contact.name)
        primary = [e for e in contact.email_ids if e.is_primary]
        self.assertEqual(len(primary), 1)
        self.assertEqual(primary[0].email_id, "b@example.com")

    # Nhiệm vụ: Gán primary cho trường không hợp lệ
    def test_set_as_primary_02(self):
        with self.assertRaises(ValidationError):
            set_as_primary(self.contact.name, "invalid", "value")

    # Nhiệm vụ: Tìm email theo keyword
    def test_search_emails_01(self):
        create_new(self.contact.name, "email", "abcsearch@example.com")
        results = search_emails("abcsearch")
        found = any("abcsearch@example.com" in r for r in results)
        self.assertTrue(found)

    # Nhiệm vụ: Lấy danh sách deals liên kết contact
    def test_get_linked_deals_empty(self):
        result = get_linked_deals(self.contact.name)
        self.assertEqual(result, [])

    # Nhiệm vụ: Tạo email đầu tiên
    def test_create_04(self):
        frappe.delete_doc("Contact", self.contact.name, force=True)
        contact = frappe.get_doc({"doctype": "Contact", "first_name": "New"})
        contact.insert()
        create_new(contact.name, "email", "first@x.com")
        c = frappe.get_doc("Contact", contact.name)
        self.assertEqual(len([e for e in c.email_ids if e.is_primary]), 1)

    # Nhiệm vụ: Thêm email thứ hai không phải primary
    def test_create_05(self):
        create_new(self.contact.name, "email", "extra@example.com")
        c = frappe.get_doc("Contact", self.contact.name)
        self.assertEqual(len([e for e in c.email_ids if e.is_primary]), 1)

    # Nhiệm vụ: Tạo số điện thoại đầu tiên
    def test_create_06(self):
        frappe.delete_doc("Contact", self.contact.name, force=True)
        contact = frappe.get_doc({"doctype": "Contact", "first_name": "New2"})
        contact.insert()
        create_new(contact.name, "mobile_no", "0123")
        c = frappe.get_doc("Contact", contact.name)
        self.assertEqual(len([p for p in c.phone_nos if p.is_primary_mobile_no]), 1)

    # Nhiệm vụ: Thêm số điện thoại thứ hai
    def test_create_07(self):
        create_new(self.contact.name, "mobile_no", "00001111222")
        c = frappe.get_doc("Contact", self.contact.name)
        self.assertEqual(len([p for p in c.phone_nos if p.is_primary_mobile_no]), 1)

    # Nhiệm vụ: Đặt số điện thoại cụ thể làm primary
    def test_set_as_primary_03(self):
        create_new(self.contact.name, "phone", "9999999999")
        set_as_primary(self.contact.name, "phone", "9999999999")
        c = frappe.get_doc("Contact", self.contact.name)
        primary = [p for p in c.phone_nos if p.is_primary_mobile_no]
        self.assertEqual(len(primary), 1)
        self.assertEqual(primary[0].phone, "9999999999")

    # Nhiệm vụ: Kiểm tra quyền khi tạo mới
    def test_permission_check_create_new(self):
        with self.assertRaises(PermissionError):
            frappe.set_user("Guest")
            create_new(self.contact.name, "email", "nope@example.com")

    # Nhiệm vụ: Kiểm tra quyền khi set primary
    def test_permission_check_set_as_primary(self):
        with self.assertRaises(PermissionError):
            frappe.set_user("Guest")
            set_as_primary(self.contact.name, "email", "test@example.com")

    # Nhiệm vụ: Kiểm tra quyền khi lấy linked deals
    def test_permission_check_get_linked_deals(self):
        with self.assertRaises(PermissionError):
            frappe.set_user("Guest")
            get_linked_deals(self.contact.name)

    # Nhiệm vụ: Tìm kiếm email không tồn tại
    def test_search_emails_02(self):
        results = search_emails("notfound@none.com")
        self.assertEqual(len(results), 0)

    # Nhiệm vụ: Đặt lại primary, kiểm tra override
    def test_set_as_primary_04(self):
        create_new(self.contact.name, "email", "a@example.com")
        create_new(self.contact.name, "email", "x@example.com")
        set_as_primary(self.contact.name, "email", "x@example.com")
        contact = frappe.get_doc("Contact", self.contact.name)
        primary_emails = [e for e in contact.email_ids if e.is_primary]
        self.assertEqual(len(primary_emails), 1)
        self.assertEqual(primary_emails[0].email_id, "x@example.com")

    # Nhiệm vụ: Đặt lại primary cho phone, kiểm tra override
    def test_set_as_primary_05(self):
        create_new(self.contact.name, "phone", "0911111111")
        create_new(self.contact.name, "phone", "0922222222")
        set_as_primary(self.contact.name, "phone", "0922222222")
        contact = frappe.get_doc("Contact", self.contact.name)
        primary_phones = [p for p in contact.phone_nos if p.is_primary_mobile_no or p.is_primary_phone]
        self.assertEqual(len(primary_phones), 1)
        self.assertEqual(primary_phones[0].phone, "0922222222")


    # Nhiệm vụ: Tạo mới số điện thoại với trường phone
    def test_create_08(self):
        result = create_new(self.contact.name, "phone", "0867867867")
        self.assertTrue(result)

    # Nhiệm vụ: Kiểm tra cập nhật email và số điện thoại trong deals khi thông tin contact thay đổi
    def test_update_deals_email_mobile_no(self):
        deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "Test Deal"
        }).insert()

        deal.append("contacts", {
            "contact": self.contact.name,
            "is_primary": 1
        })
        deal.save()

        self.contact.email_id = "updated@example.com"
        self.contact.mobile_no = "0999999999"
        self.contact.save()

        updated_deal = frappe.get_doc("CRM Deal", deal.name)
        self.assertEqual(updated_deal.email, "updated@example.com")
        self.assertEqual(updated_deal.mobile_no, "0999999999")

        # Cleanup
        frappe.delete_doc("CRM Deal", deal.name, force=True)

if __name__ == "__main__":
    unittest.main()
