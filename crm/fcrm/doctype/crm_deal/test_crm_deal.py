import frappe
import unittest
import uuid
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import PermissionError, DoesNotExistError, LinkValidationError
from unittest.mock import patch
from crm.api.activity import create_deal
from crm.fcrm.doctype.crm_deal.crm_deal import (
    create_contact, add_contact, remove_contact, set_primary_contact, contact_exists
)

# Kiểm thử chức năng tạo Deal trong CRM
class TestCreateDealFunction(unittest.TestCase):

    # Thiết lập môi trường trước mỗi bài kiểm thử
    def setUp(self):
        frappe.set_user("Administrator")  # Đảm bảo rằng người dùng là Admin để có quyền tạo tài liệu
        self.organization_name = f"Test Org {uuid.uuid4()}"  # Tạo tên tổ chức ngẫu nhiên
        self.organization = frappe.get_doc({
            "doctype": "CRM Organization",  # Tạo tổ chức CRM mới
            "organization_name": self.organization_name,
            "no_of_employees": "1-10"
        }).insert(ignore_permissions=True)

        self.contact_email = f"alice_{uuid.uuid4().hex[:6]}@example.com"  # Tạo email ngẫu nhiên cho contact
        self.contact = frappe.get_doc({
            "doctype": "Contact",  # Tạo liên hệ mới
            "first_name": "Alice",
            "last_name": "Nguyen",
            "email_id": self.contact_email,
            "mobile_no": "0123456789"
        }).insert(ignore_permissions=True)

    # Quay lại trạng thái ban đầu sau mỗi bài kiểm thử
    def tearDown(self):
        frappe.db.rollback()

    # Kiểm thử việc tạo Deal với tổ chức và liên hệ đã tồn tại
    def test_create_deal_with_existing_contact_and_organization(self):
        deal_data = {
            "deal_name": f"Test Deal {uuid.uuid4()}",
            "deal_value": 10000,
            "deal_stage": "Qualified",
            "organization": self.organization.name,
            "contact": self.contact.name,
        }

        deal_name = create_deal(deal_data)  # Gọi hàm tạo Deal

        self.assertTrue(frappe.db.exists("CRM Deal", deal_name))  # Kiểm tra Deal có tồn tại trong cơ sở dữ liệu
        deal_doc = frappe.get_doc("CRM Deal", deal_name)
        self.assertEqual(deal_doc.organization, self.organization.name)  # Kiểm tra tổ chức của Deal
        self.assertEqual(deal_doc.contacts[0].contact, self.contact.name)  # Kiểm tra liên hệ trong Deal


# Kiểm thử tạo Deal khi không có tổ chức và liên hệ
class TestCreateDealWithoutOrgAndContact(unittest.TestCase):

    def setUp(self):
        frappe.set_user("Administrator")
        self.deal_data = {
            "deal_name": f"Auto Deal {uuid.uuid4()}",
            "deal_value": 5000,
            "deal_stage": "Lead",
            "first_name": "Bob",
            "last_name": "Tran",
            "email": f"bob_{uuid.uuid4().hex[:6]}@example.com",
            "mobile_no": "0987654321",
            "organization_name": f"Auto Org {uuid.uuid4().hex[:6]}",
            "no_of_employees": "11-50",
        }

    def tearDown(self):
        frappe.db.rollback()

    def test_create_deal_without_org_and_contact(self):
        deal_name = create_deal(self.deal_data)  # Gọi hàm tạo Deal
        deal_doc = frappe.get_doc("CRM Deal", deal_name)

        self.assertTrue(frappe.db.exists("CRM Deal", deal_name))  # Kiểm tra Deal đã được tạo
        self.assertTrue(frappe.db.exists("CRM Organization", deal_doc.organization))  # Kiểm tra tổ chức đã được tạo
        self.assertGreater(len(deal_doc.contacts), 0)  # Kiểm tra có ít nhất một liên hệ trong Deal

        contact = frappe.get_doc("Contact", deal_doc.contacts[0].contact)  # Lấy thông tin liên hệ
        self.assertEqual(contact.email_id, self.deal_data["email"])  # Kiểm tra email liên hệ
        self.assertEqual(contact.mobile_no, self.deal_data["mobile_no"])  # Kiểm tra số điện thoại liên hệ


# Kiểm thử tạo Deal chỉ với liên hệ, không có tổ chức
class TestCreateDealWithoutOrganization(FrappeTestCase):
    def test_create_deal_with_contact_only(self):
        args = {
            "title": "Deal With Contact Only",
            "first_name": "NoOrg",
            "last_name": "User",
            "email": "noorguser@example.com",
            "mobile_no": "0987654321"
        }

        deal_name = create_deal(args)  # Gọi hàm tạo Deal
        deal = frappe.get_doc("CRM Deal", deal_name)

        self.assertFalse(deal.organization)  # Kiểm tra rằng Deal không có tổ chức
        self.assertGreater(len(deal.contacts), 0)  # Kiểm tra có ít nhất một liên hệ trong Deal

        contact = frappe.get_doc("Contact", deal.contacts[0].contact)  # Lấy thông tin liên hệ
        self.assertEqual(contact.first_name, "NoOrg")  # Kiểm tra tên liên hệ
        self.assertEqual(contact.email_ids[0].email_id, "noorguser@example.com")  # Kiểm tra email liên hệ


# Kiểm thử tạo Contact với các trường hợp khác nhau
class TestCreateContact(unittest.TestCase):

    # Kiểm thử tạo Contact với tất cả các trường
    def test_create_contact_with_all_fields(self):
        doc = {
            "first_name": "John",
            "last_name": "Doe",
            "salutation": "Mr",
            "organization": "TechCorp",
            "email": "john.doe@techcorp.com",
            "mobile_no": "1234567890"
        }

        contact_name = create_contact(doc)  # Gọi hàm tạo Contact
        contact = frappe.get_doc("Contact", contact_name)

        self.assertEqual(contact.first_name, "John")  # Kiểm tra tên đầu tiên
        self.assertEqual(contact.last_name, "Doe")  # Kiểm tra họ
        self.assertEqual(contact.company_name, "TechCorp")  # Kiểm tra tên công ty
        self.assertEqual(contact.email_ids[0].email_id, "john.doe@techcorp.com")  # Kiểm tra email
        self.assertEqual(contact.phone_nos[0].phone, "1234567890")  # Kiểm tra số điện thoại

    # Kiểm thử tạo Contact khi thiếu email và số điện thoại
    def test_create_contact_with_missing_email_and_phone(self):
        doc = {
            "first_name": "Jane",
            "last_name": "Smith",
            "organization": "AnotherCorp"
        }

        contact_name = create_contact(doc)  # Gọi hàm tạo Contact
        contact = frappe.get_doc("Contact", contact_name)

        self.assertEqual(contact.first_name, "Jane")  # Kiểm tra tên đầu tiên
        self.assertEqual(contact.last_name, "Smith")  # Kiểm tra họ
        self.assertEqual(len(contact.email_ids), 0)  # Kiểm tra không có email
        self.assertEqual(len(contact.phone_nos), 0)  # Kiểm tra không có số điện thoại

    # Kiểm thử tạo Contact với liên hệ đã tồn tại
    def test_create_contact_with_existing_contact(self):
        doc = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@techcorp.com",
            "mobile_no": "1234567890"
        }

        create_contact(doc)  # Tạo liên hệ ban đầu
        contact_name = create_contact(doc)  # Tạo liên hệ trùng

        self.assertEqual(contact_name, doc["email"])  # Kiểm tra rằng tên liên hệ bằng email (giả sử tên = email)

    # Kiểm thử tạo Contact với dữ liệu không hợp lệ
    def test_create_contact_with_invalid_data(self):
        doc = {"first_name": None, "last_name": None}  # Dữ liệu thiếu
        with self.assertRaises(frappe.ValidationError):  # Kiểm tra ngoại lệ ValidationError
            create_contact(doc)


# Kiểm thử thêm liên hệ vào Deal
class TestAddContact(unittest.TestCase):
    # Thiết lập môi trường kiểm thử
    def setUp(self):
        frappe.set_user("Administrator")
        self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Test"}).insert(ignore_permissions=True)
        self.deal = frappe.get_doc({"doctype": "CRM Deal", "deal_name": "Test Deal"}).insert(ignore_permissions=True)

    # Quay lại trạng thái ban đầu sau bài kiểm thử
    def tearDown(self):
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)

    # Kiểm thử thêm liên hệ vào Deal thành công
    def test_add_contact_success(self):
        result = add_contact(self.deal.name, self.contact.name)  # Gọi hàm thêm liên hệ
        updated = frappe.get_doc("CRM Deal", self.deal.name)  # Lấy thông tin Deal đã cập nhật
        contact_names = [c.contact for c in updated.contacts]
        self.assertTrue(result)  # Kiểm tra hàm trả về True
        self.assertIn(self.contact.name, contact_names)  # Kiểm tra liên hệ đã được thêm vào Deal

    # Kiểm thử khi không có quyền thêm liên hệ
    def test_add_contact_no_permission(self):
        with patch("frappe.has_permission", return_value=False):  # Giả lập không có quyền
            with self.assertRaises(PermissionError):  # Kiểm tra ngoại lệ PermissionError
                add_contact(self.deal.name, self.contact.name)

    # Kiểm thử khi Deal không tồn tại
    def test_add_contact_deal_not_found(self):
        with self.assertRaises(DoesNotExistError):  # Kiểm tra ngoại lệ DoesNotExistError
            add_contact("Nonexistent Deal", self.contact.name)

    # Kiểm thử khi liên hệ không tồn tại
    def test_add_contact_contact_not_found(self):
        with self.assertRaises(LinkValidationError):  # Kiểm tra ngoại lệ LinkValidationError
            add_contact(self.deal.name, "Nonexistent Contact")


class TestRemoveContact(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        # Tạo mới contact và deal
        self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Jane"}).insert(ignore_permissions=True)
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "Deal With Contact",
            "contacts": [{"contact": self.contact.name}]
        }).insert(ignore_permissions=True)

    def tearDown(self):
        # Xóa các đối tượng đã tạo sau khi kiểm thử
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)

    def test_remove_contact_success(self):
        # Kiểm tra thành công khi xóa contact khỏi deal
        result = remove_contact(self.deal.name, self.contact.name)
        updated = frappe.get_doc("CRM Deal", self.deal.name)
        self.assertTrue(result)
        self.assertNotIn(self.contact.name, [c.contact for c in updated.contacts])

    def test_remove_contact_no_permission(self):
        # Kiểm tra trường hợp không có quyền khi xóa contact
        with patch("frappe.has_permission", return_value=False):
            with self.assertRaises(PermissionError):
                remove_contact(self.deal.name, self.contact.name)

    def test_remove_contact_deal_not_found(self):
        # Kiểm tra trường hợp deal không tồn tại
        with self.assertRaises(DoesNotExistError):
            remove_contact("Nonexistent Deal", self.contact.name)

    def test_remove_contact_not_in_list(self):
        # Kiểm tra trường hợp contact không có trong danh sách của deal
        another_deal = frappe.get_doc({"doctype": "CRM Deal", "deal_name": "No Contact Deal"}).insert(ignore_permissions=True)
        try:
            result = remove_contact(another_deal.name, self.contact.name)
            self.assertTrue(result)
        finally:
            frappe.delete_doc("CRM Deal", another_deal.name, force=True)

class TestSetPrimaryContact(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        # Tạo mới contact và deal
        self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Primary"}).insert(ignore_permissions=True)
        self.other_contact = frappe.get_doc({"doctype": "Contact", "first_name": "Other"}).insert(ignore_permissions=True)
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "Primary Deal",
            "contacts": [
                {"contact": self.contact.name, "is_primary": 0},
                {"contact": self.other_contact.name, "is_primary": 1}
            ]
        }).insert(ignore_permissions=True)

    def tearDown(self):
        # Xóa các đối tượng đã tạo sau khi kiểm thử
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)
        frappe.delete_doc("Contact", self.other_contact.name, force=True)

    def test_set_primary_contact_success(self):
        # Kiểm tra thành công khi set primary contact
        result = set_primary_contact(self.deal.name, self.contact.name)
        updated = frappe.get_doc("CRM Deal", self.deal.name)
        self.assertTrue(result)
        for c in updated.contacts:
            if c.contact == self.contact.name:
                self.assertEqual(c.is_primary, 1)
            else:
                self.assertNotEqual(c.is_primary, 1)

    def test_set_primary_contact_no_permission(self):
        # Kiểm tra trường hợp không có quyền khi set primary contact
        with patch("frappe.has_permission", return_value=False):
            with self.assertRaises(PermissionError):
                set_primary_contact(self.deal.name, self.contact.name)

    def test_set_primary_contact_deal_not_found(self):
        # Kiểm tra trường hợp deal không tồn tại
        with self.assertRaises(DoesNotExistError):
            set_primary_contact("InvalidDeal", self.contact.name)

    def test_set_primary_contact_contact_not_in_list(self):
        # Kiểm tra trường hợp contact không có trong danh sách của deal
        outside_contact = frappe.get_doc({"doctype": "Contact", "first_name": "Outside"}).insert(ignore_permissions=True)
        try:
            with self.assertRaises(Exception):
                set_primary_contact(self.deal.name, outside_contact.name)
        finally:
            frappe.delete_doc("Contact", outside_contact.name, force=True)

class TestContactExists(unittest.TestCase):
    @patch("frappe.db.get_value")
    @patch("frappe.db.exists")
    def test_contact_exists_with_email(self, mock_exists, mock_get_value):
        # Kiểm tra khi tìm kiếm contact qua email
        doc = {"email": "test@example.com", "mobile_no": "123456789"}
        mock_exists.side_effect = ["contact_email_name", None]
        mock_get_value.return_value = "Parent Contact A"
        result = contact_exists(doc)
        self.assertEqual(result, "Parent Contact A")

    @patch("frappe.db.get_value")
    @patch("frappe.db.exists")
    def test_contact_exists_with_phone(self, mock_exists, mock_get_value):
        # Kiểm tra khi tìm kiếm contact qua số điện thoại
        doc = {"email": "test@example.com", "mobile_no": "123456789"}
        mock_exists.side_effect = [None, "contact_phone_name"]
        mock_get_value.return_value = "Parent Contact B"
        result = contact_exists(doc)
        self.assertEqual(result, "Parent Contact B")

    @patch("frappe.db.exists")
    def test_contact_exists_no_match(self, mock_exists):
        # Kiểm tra khi không tìm thấy contact nào
        doc = {"email": "none@example.com", "mobile_no": "000000000"}
        mock_exists.side_effect = [None, None]
        result = contact_exists(doc)
        self.assertFalse(result)
