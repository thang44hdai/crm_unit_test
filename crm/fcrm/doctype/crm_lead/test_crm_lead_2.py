import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError, PermissionError
from crm.fcrm.doctype.crm_lead.crm_lead import CRMLead, convert_to_deal
from crm.fcrm.doctype.crm_lead.api import get_lead

class TestCRMLeadFunctions(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.begin()
        
        # Tạo lead cơ bản cho tất cả test cases
        self.lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "Test",
            "last_name": "Lead",
            "email": "test.lead@example.com",
            "phone": "0123456789",
            "status": "New"
        }).insert(ignore_permissions=True)
    
    def tearDown(self):
        frappe.db.rollback()
    
    def test_get_lead_api(self):
        """Test API lấy thông tin Lead"""
        # Lấy thông tin lead từ API
        lead_data = get_lead(self.lead.name)
        
        # Kiểm tra thông tin cơ bản
        self.assertEqual(lead_data.get("name"), self.lead.name)
        self.assertEqual(lead_data.get("first_name"), "Test")
        self.assertEqual(lead_data.get("last_name"), "Lead")
        self.assertEqual(lead_data.get("email"), "test.lead@example.com")
        self.assertEqual(lead_data.get("status"), "New")
        
        # Kiểm tra các thông tin meta được thêm vào
        self.assertTrue("fields_meta" in lead_data)
        self.assertTrue("_form_script" in lead_data)
        self.assertTrue("_assign" in lead_data)
        
        # Kiểm tra cấu trúc của fields_meta
        self.assertIsInstance(lead_data.get("fields_meta"), dict)
        
        # Kiểm tra quyền truy cập trường hợp không có quyền
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            lead_data = get_lead(self.lead.name)
        frappe.set_user("Administrator")
    
 
    def test_assign_agent(self):
        """Test phân công người đại diện cho Lead"""
        # Tạo user mới nếu chưa tồn tại
        if not frappe.db.exists("User", "test.agent@example.com"):
            frappe.get_doc({
                "doctype": "User",
                "email": "test.agent@example.com",
                "first_name": "Test",
                "last_name": "Agent",
                "send_welcome_email": 0,
                "roles": [{"role": "System Manager"}]
            }).insert(ignore_permissions=True)
        
        # Phân công người đại diện
        self.lead.assign_agent("test.agent@example.com")
        
        # Kiểm tra xem nhiệm vụ đã được gán chưa
        assigned_users = self.lead.get_assigned_users()
        self.assertTrue("test.agent@example.com" in assigned_users)
   
    def test_convert_to_deal(self):
        """Test chuyển đổi Lead thành Deal"""
        # Chuẩn bị dữ liệu
        if not frappe.db.exists("User", "test.agent@example.com"):
            frappe.get_doc({
                "doctype": "User",
                "email": "test.agent@example.com",
                "first_name": "Test",
                "last_name": "Agent",
                "send_welcome_email": 0,
                "roles": [{"role": "System Manager"}]
            }).insert(ignore_permissions=True)
        
        self.lead.lead_owner = "test.agent@example.com"
        self.lead.organization = f"Test Org {frappe.utils.random_string(8)}"
        self.lead.email = f"unique.{frappe.utils.random_string(8)}@example.com"
        self.lead.save()
        
        # Thực hiện chuyển đổi
        deal_name = convert_to_deal(lead=self.lead.name)
        
        # Kiểm tra Deal đã được tạo
        self.assertTrue(frappe.db.exists("CRM Deal", deal_name))
        
        # Kiểm tra Lead đã được đánh dấu đã chuyển đổi
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        self.assertEqual(lead.converted, 1)
        
        # Kiểm tra thông tin Deal
        deal = frappe.get_doc("CRM Deal", deal_name)
        self.assertEqual(deal.lead, self.lead.name)
        self.assertEqual(deal.organization, lead.organization)
        self.assertEqual(deal.deal_owner, lead.lead_owner)
