from types import SimpleNamespace
import uuid
import frappe
import unittest
from frappe.exceptions import DoesNotExistError, LinkValidationError, PermissionError
from crm.fcrm.doctype.crm_deal.api import (
    get_deal_contacts, get_deal,
)
from unittest.mock import MagicMock, patch
from crm.fcrm.doctype.crm_deal.crm_deal import (
    create_deal, add_contact, 
    remove_contact, set_primary_contact,
    create_contact, contact_exists,
    create_organization
)

class TestCreateDealWithExistingContactAndOrganization(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.organization_name = f"Test Org {uuid.uuid4()}"
        self.organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": self.organization_name,
            "no_of_employees": "1-10"
        }).insert(ignore_permissions=True)

        self.contact_email = f"alice_{uuid.uuid4().hex[:6]}@example.com"
        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Alice",
            "last_name": "Nguyen",
            "email_id": self.contact_email,
            "mobile_no": "0123456789"
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    # Nhiệm vụ: Kiểm tra tạo deal với contact và organization đã tồn tại
    def test_create_deal_01(self):
        deal_data = {
            "deal_name": f"Test Deal {uuid.uuid4()}",
            "deal_value": 10000,
            "deal_stage": "Qualified",
            "organization": self.organization.name,
            "contact": self.contact.name,
        }

        deal_name = create_deal(deal_data)

        self.assertTrue(frappe.db.exists("CRM Deal", deal_name))

        deal_doc = frappe.get_doc("CRM Deal", deal_name)
        self.assertEqual(deal_doc.organization, self.organization.name)
        self.assertEqual(deal_doc.contacts[0].contact, self.contact.name)

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

    # Nhiệm vụ: Kiểm tra tạo deal khi chưa có sẵn contact và organization
    def test_create_deal_02(self):
        deal_name = create_deal(self.deal_data)
        deal_doc = frappe.get_doc("CRM Deal", deal_name)

        self.assertTrue(frappe.db.exists("CRM Deal", deal_name))

        self.assertTrue(frappe.db.exists("CRM Organization", deal_doc.organization))
        self.assertGreater(len(deal_doc.contacts), 0)

        contact = frappe.get_doc("Contact", deal_doc.contacts[0].contact)
        self.assertEqual(contact.email_id, self.deal_data["email"])
        self.assertEqual(contact.mobile_no, self.deal_data["mobile_no"])

class TestAddContact(unittest.TestCase):

    def setUp(self):
        frappe.set_user("Administrator")
        self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Test"}).insert(ignore_permissions=True)
        self.deal = frappe.get_doc({"doctype": "CRM Deal", "deal_name": "Test Deal"}).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)

    # Nhiệm vụ: Kiểm tra thêm contact vào deal
    def test_add_contact_01(self):
        result = add_contact(self.deal.name, self.contact.name)
        updated = frappe.get_doc("CRM Deal", self.deal.name)
        contact_names = [c.contact for c in updated.contacts]

        self.assertTrue(result)
        self.assertIn(self.contact.name, contact_names)

    # Nhiệm vụ: Kiểm tra quyền truy cập khi thêm contact vào deal
    def test_add_contact_04(self):
        with patch("frappe.has_permission", return_value=False):
            with self.assertRaises(PermissionError):  
                add_contact(self.deal.name, self.contact.name)

    # Nhiệm vụ: Kiểm tra xử lý khi thêm contact vào deal không tồn tại
    def test_add_contact_02(self):
        with self.assertRaises(DoesNotExistError): 
            add_contact("Nonexistent Deal", self.contact.name)

    # Nhiệm vụ: Kiểm tra xử lý khi thêm contact không tồn tại vào deal
    def test_add_contact_03(self):
        with self.assertRaises(LinkValidationError):  
            add_contact(self.deal.name, "Nonexistent Contact")

class TestRemoveContact(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Jane"}).insert(ignore_permissions=True)
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "Deal With Contact",
            "contacts": [{"contact": self.contact.name}]
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)

    # Nhiệm vụ: Kiểm tra xóa contact khỏi deal
    def test_remove_contact_01(self):
        result = remove_contact(self.deal.name, self.contact.name)
        updated = frappe.get_doc("CRM Deal", self.deal.name)
        self.assertTrue(result)
        self.assertNotIn(self.contact.name, [c.contact for c in updated.contacts])

    # Nhiệm vụ: Kiểm tra quyền truy cập khi xóa contact khỏi deal
    def test_remove_contact_04(self):
        with patch("frappe.has_permission", return_value=False):
            with self.assertRaises(PermissionError):
                remove_contact(self.deal.name, self.contact.name)

    # Nhiệm vụ: Kiểm tra xử lý khi xóa contact khỏi deal không tồn tại
    def test_remove_contact_02(self):
        with self.assertRaises(DoesNotExistError):
            remove_contact("Nonexistent Deal", self.contact.name)

    # Nhiệm vụ: Kiểm tra xử lý khi xóa contact không có trong danh sách contacts của deal
    def test_remove_contact_03(self):
        another_deal = frappe.get_doc({"doctype": "CRM Deal", "deal_name": "No Contact Deal"}).insert(ignore_permissions=True)
        try:
            result = remove_contact(another_deal.name, self.contact.name)
            self.assertTrue(result)
        finally:
            frappe.delete_doc("CRM Deal", another_deal.name, force=True)

class TestSetPrimaryContact(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
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
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)
        frappe.delete_doc("Contact", self.other_contact.name, force=True)

    # Nhiệm vụ: Kiểm tra thiết lập contact chính cho deal
    def test_set_primary_contact_01(self):
        result = set_primary_contact(self.deal.name, self.contact.name)
        updated = frappe.get_doc("CRM Deal", self.deal.name)
        self.assertTrue(result)
        for c in updated.contacts:
            if c.contact == self.contact.name:
                self.assertEqual(c.is_primary, 1)
            else:
                self.assertNotEqual(c.is_primary, 1)

    # Nhiệm vụ: Kiểm tra quyền truy cập khi thiết lập contact chính cho deal
    def test_set_primary_contact_04(self):
        with patch("frappe.has_permission", return_value=False):
            with self.assertRaises(PermissionError):
                set_primary_contact(self.deal.name, self.contact.name)

    # Nhiệm vụ: Kiểm tra xử lý khi thiết lập contact chính cho deal không tồn tại
    def test_set_primary_contact_02(self):
        with self.assertRaises(DoesNotExistError):
            set_primary_contact("InvalidDeal", self.contact.name)

    # Nhiệm vụ: Kiểm tra xử lý khi thiết lập contact chính cho deal với contact không có trong danh sách
    def test_set_primary_contact_03(self):
        outside_contact = frappe.get_doc({"doctype": "Contact", "first_name": "Outside"}).insert(ignore_permissions=True)
        try:
            with self.assertRaises(Exception):
                set_primary_contact(self.deal.name, outside_contact.name)
        finally:
            frappe.delete_doc("Contact", outside_contact.name, force=True)

class TestGetDeal(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "Test Deal"
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)

    # Nhiệm vụ: Kiểm tra lấy thông tin của deal
    def test_get_deal_01(self):
        result = get_deal(self.deal.name)

        self.assertEqual(result["name"], self.deal.name)
        self.assertIn("fields_meta", result)
        self.assertIn("_form_script", result)
        self.assertIn("_assign", result)

    # Nhiệm vụ: Kiểm tra xử lý khi lấy thông tin deal không tồn tại
    def test_get_deal_02(self):
        with self.assertRaises(frappe.DoesNotExistError):
            get_deal("Nonexistent Deal")

class TestGetDealContacts(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Contact A",
            "email_ids": [{"email_id": "contacta@example.com", "is_primary": 1}],
            "phone_nos": [{"phone": "0123456789", "is_primary": 1}],
        }).insert(ignore_permissions=True)

        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": f"Deal_{uuid.uuid4().hex[:6]}",
            "contacts": [{"contact": self.contact.name, "is_primary": 1}]
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.delete_doc("CRM Deal", self.deal.name, force=True)
        frappe.delete_doc("Contact", self.contact.name, force=True)

    # Nhiệm vụ: Kiểm tra lấy danh sách contacts của deal
    def test_get_deal_contacts_01(self):
        contacts = get_deal_contacts(self.deal.name)

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["name"], self.contact.name)  
        self.assertEqual(contacts[0]["email"], "contacta@example.com")
        self.assertEqual(contacts[0]["mobile_no"], "0123456789")

    # Nhiệm vụ: Kiểm tra lấy danh sách contacts của deal không có contact nào
    def test_get_deal_contacts_02(self):
        empty_deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": f"Empty_{uuid.uuid4().hex[:6]}"
        }).insert(ignore_permissions=True)

        try:
            contacts = get_deal_contacts(empty_deal.name)

            self.assertEqual(contacts, [])
        finally:
            frappe.delete_doc("CRM Deal", empty_deal.name, force=True)

    # Nhiệm vụ: Kiểm tra xử lý khi lấy danh sách contacts của deal không tồn tại
    def test_get_deal_contacts_03(self):
        with self.assertRaises(frappe.DoesNotExistError):
            get_deal_contacts("Invalid Deal Name")

class TestContactExists(unittest.TestCase):

    # Nhiệm vụ: Kiểm tra tìm kiếm contact bằng email
    @patch("frappe.db.get_value")
    @patch("frappe.db.exists")
    def test_contact_exists_01(self, mock_exists, mock_get_value):
        doc = {
            "email": "john.doe@example.com",
            "mobile_no": None
        }
        mock_exists.return_value = True
        mock_get_value.return_value = "CONT0001"

        result = contact_exists(doc) 
        self.assertTrue(result)
        mock_exists.assert_called_once_with(
            "Contact Email", 
            {"email_id": doc["email"]}
        )

    # Nhiệm vụ: Kiểm tra tìm kiếm contact bằng số điện thoại
    @patch("frappe.db.get_value")
    @patch("frappe.db.exists")
    def test_contact_exists_02(self, mock_exists, mock_get_value):
        doc = {
            "email": None,
            "mobile_no": "0123456789"
        }
        mock_exists.return_value = True
        mock_get_value.return_value = "CONT0002"

        result = contact_exists(doc)
        self.assertTrue(result)
        mock_exists.assert_called_once_with(
            "Contact Phone", 
            {"phone": doc["mobile_no"]}
        )

    # Nhiệm vụ: Kiểm tra xử lý khi contact không tồn tại
    @patch("frappe.db.exists")
    def test_contact_exists_03(self, mock_exists):
        doc = {
            "email": "nonexistent@example.com",
            "mobile_no": None
        }
        mock_exists.return_value = False

        result = contact_exists(doc)
        self.assertFalse(result)

class TestCreateContact(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.doc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "salutation": "Mr",
            "organization": "Test Org",
            "email": "john.doe@example.com",
            "mobile_no": "0123456789"
        }
        self.third = {
            "first_name": "John",
            "last_name": "Doe",
            "salutation": "Mr",
            "organization": "Test Org",
            "mobile_no": "0123456789"
        }
        self.second = {
            "first_name": "John",
            "last_name": "Doe",
            "salutation": "Mr",
            "organization": "Test Org",
            "email": "john.doe@example.com",
        }

    def tearDown(self):
        frappe.db.rollback()

    # Nhiệm vụ: Kiểm tra tạo mới contact
    def test_create_contact_01(self):
        contact_name = create_contact(self.doc_data)
        contact = frappe.get_doc("Contact", contact_name)
        
        self.assertEqual(contact.first_name, self.doc_data["first_name"])
        self.assertEqual(contact.last_name, self.doc_data["last_name"])
        self.assertEqual(contact.salutation, self.doc_data["salutation"])
        self.assertEqual(contact.company_name, self.doc_data["organization"])
        
        self.assertTrue(any(e.email_id == self.doc_data["email"] and e.is_primary == 1 
                        for e in contact.email_ids))
        
        self.assertTrue(any(p.phone == self.doc_data["mobile_no"] and p.is_primary_mobile_no == 1 
                        for p in contact.phone_nos))

    # Nhiệm vụ: Kiểm tra tìm kiếm contact đã tồn tại
    @patch("frappe.db.exists")
    @patch("frappe.db.get_value")
    def test_create_contact_04(self, mock_get_value, mock_exists):
        mock_exists.return_value = True
        mock_get_value.return_value = "CONT0001"
        
        result = create_contact(self.doc_data)
        self.assertEqual(result, "CONT0001")
        mock_exists.assert_called_once()

    # Nhiệm vụ: Kiểm tra tạo contact có với email
    def test_create_contact_02(self):
        contact_name = create_contact(self.second)
        contact = frappe.get_doc("Contact", contact_name)
        self.assertTrue(any(e.email_id == self.doc_data["email"] and e.is_primary == 1 
                        for e in contact.email_ids))

    # Nhiệm vụ: Kiểm tra tạo contact có số điện thoại
    def test_create_contact_03(self):
        contact_name = create_contact(self.third)
        contact = frappe.get_doc("Contact", contact_name)
        self.assertTrue(any(p.phone == self.doc_data["mobile_no"] and p.is_primary_mobile_no == 1 
                        for p in contact.phone_nos))

class TestCreateOrganization(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.org_data = {
            "organization_name": "Test Organization",
            "website": "www.test.com",
            "industry": "Technology",
            "annual_revenue": 1000000
        }

    def tearDown(self):
        frappe.db.rollback()

    # Nhiệm vụ: Kiểm tra tạo mới organization với đầy đủ thông tin
    def test_create_organization_01(self):
        org_name = create_organization(self.org_data)
        org = frappe.get_doc("CRM Organization", org_name)
        
        self.assertEqual(org.organization_name, self.org_data["organization_name"])
        self.assertEqual(org.website, self.org_data["website"])
        self.assertEqual(org.territory, self.org_data["territory"])
        self.assertEqual(org.industry, self.org_data["industry"])
        self.assertEqual(org.annual_revenue, self.org_data["annual_revenue"])

    # Nhiệm vụ: Kiểm tra xử lý khi không cung cấp organization_name
    def test_create_organization_03(self):
        result = create_organization({})
        self.assertIsNone(result)

    # Nhiệm vụ: Kiểm tra xử lý khi organization đã tồn tại
    @patch("frappe.db.exists")
    def test_create_organization_04(self, mock_exists):
        mock_exists.return_value = "ORG0001"
        
        result = create_organization(self.org_data)
        self.assertEqual(result, "ORG0001")
        mock_exists.assert_called_once_with(
            "CRM Organization", 
            {"organization_name": self.org_data["organization_name"]}
        )

    # Nhiệm vụ: Kiểm tra tạo organization với tên chứa ký tự đặc biệt
    def test_create_organization_02(self):
        special_data = {
            "organization_name": "Test & Company (Pvt.) Ltd.",
            "website": "www.test.com",
            "industry": "Technology",
            "annual_revenue": 1000000
        }
        org_name = create_organization(special_data)
        org = frappe.get_doc("CRM Organization", org_name)
        self.assertEqual(org.organization_name, special_data["organization_name"])

class TestAssignAgent(unittest.TestCase):

    def setUp(self):
        frappe.set_user("Administrator")
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "DEAL-0001"
        }).insert(ignore_permissions=True)

    # Nhiệm vụ: Kiểm tra gán agent cho deal khi chưa có assignee nào
    @patch("crm.fcrm.doctype.crm_deal.crm_deal.assign")
    def test_assign_agent_01(self, mock_assign):
        self.deal.get_assigned_users = MagicMock(return_value=[])
        self.deal.assign_agent("agent1")
        mock_assign.assert_called_once_with(
            {"assign_to": ["agent1"], "doctype": "CRM Deal", "name": "DEAL-0001"},
            ignore_permissions=True
        )

    # Nhiệm vụ: Kiểm tra không gán lại agent nếu agent đã là assignee
    @patch("crm.fcrm.doctype.crm_deal.crm_deal.assign")
    def test_assign_agent_02(self, mock_assign):
        self.deal.get_assigned_users = MagicMock(return_value=["agent1"])
        self.deal.assign_agent("agent1")
        mock_assign.assert_not_called()

    # Nhiệm vụ: Kiểm tra không thực hiện gì nếu agent là None
    def test_assign_agent_03(self):
        self.deal.get_assigned_users = MagicMock()
        self.assertIsNone(self.deal.assign_agent(None))


class TestShareWithAgent(unittest.TestCase):

    def setUp(self):
        frappe.set_user("Administrator")
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "DEAL-0001"
        }).insert(ignore_permissions=True)

    # Nhiệm vụ: Kiểm tra phân quyền chia sẻ deal cho agent mới
    @patch("frappe.share.add_docshare")
    @patch("frappe.db.exists")
    @patch("frappe.get_all")
    @patch("frappe.share.remove")
    def test_share_with_agent_01(self, mock_remove, mock_get_all, mock_exists, mock_add_docshare):
        mock_get_all.return_value = [SimpleNamespace(user="old_user")]
        mock_exists.return_value = False
        self.deal.share_with_agent("agent1")
        mock_add_docshare.assert_called_once()
        mock_remove.assert_called_once_with("CRM Deal", "DEAL-0001", "old_user")

    # Nhiệm vụ: Kiểm tra không chia sẻ lại nếu agent đã được share
    @patch("frappe.share.add_docshare")
    @patch("frappe.db.exists")
    @patch("frappe.get_all")
    @patch("frappe.share.remove")
    def test_share_with_agent_02(self, mock_remove, mock_get_all, mock_exists, mock_add_docshare):
        mock_get_all.return_value = [SimpleNamespace(user="old_user")]
        mock_exists.return_value = True
        self.deal.share_with_agent("agent1")
        mock_add_docshare.assert_not_called()
        mock_remove.assert_not_called()

    # Nhiệm vụ: Kiểm tra không thực hiện gì nếu agent là None
    def test_share_with_agent_03(self):
        self.assertIsNone(self.deal.share_with_agent(None))

class TestSetPrimaryEmailMobileNo(unittest.TestCase):
    def setUp(self):
        self.deal = frappe.get_doc({
            "doctype": "CRM Deal",
            "deal_name": "Test Deal"
        }).insert(ignore_permissions=True)
        self.deal.contacts = []

    # Nhiệm vụ: Kiểm tra khi không có contact nào
    def test_no_contacts(self):
        self.deal.set_primary_email_mobile_no()
        self.assertEqual(self.deal.email, "")
        self.assertEqual(self.deal.mobile_no, "")
        self.assertEqual(self.deal.phone, "")

    # Nhiệm vụ: Kiểm tra khi có 1 contact là primary
    def test_one_primary_contact(self):
        contact = MagicMock()
        contact.is_primary = 1
        contact.email = "a@b.com"
        contact.mobile_no = "123"
        contact.phone = "456"
        self.deal.contacts = [contact]
        self.deal.set_primary_email_mobile_no()
        self.assertEqual(self.deal.email, "a@b.com")
        self.assertEqual(self.deal.mobile_no, "123")
        self.assertEqual(self.deal.phone, "456")

    # Nhiệm vụ: Kiểm tra khi có nhiều contact, chỉ 1 contact là primary
    def test_multiple_contacts_one_primary(self):
        c1 = MagicMock()
        c1.is_primary = 0
        c1.email = "x@x.com"
        c1.mobile_no = "111"
        c1.phone = "222"
        c2 = MagicMock()
        c2.is_primary = 1
        c2.email = "y@y.com"
        c2.mobile_no = "333"
        c2.phone = "444"
        self.deal.contacts = [c1, c2]
        self.deal.set_primary_email_mobile_no()
        self.assertEqual(self.deal.email, "y@y.com")
        self.assertEqual(self.deal.mobile_no, "333")
        self.assertEqual(self.deal.phone, "444")

    # Nhiệm vụ: Kiểm tra khi có nhiều hơn 1 contact là primary
    def test_multiple_primary_contacts(self):
        c1 = MagicMock()
        c1.is_primary = 1
        c1.email = "x@x.com"
        c1.mobile_no = "111"
        c1.phone = "222"
        c2 = MagicMock()
        c2.is_primary = 1
        c2.email = "y@y.com"
        c2.mobile_no = "333"
        c2.phone = "444"
        self.deal.contacts = [c1, c2]
        with self.assertRaises(frappe.ValidationError):
            self.deal.set_primary_email_mobile_no()