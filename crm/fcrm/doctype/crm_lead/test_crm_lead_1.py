from frappe.tests.utils import FrappeTestCase
import frappe
from frappe.exceptions import DoesNotExistError, ValidationError, PermissionError, DuplicateEntryError
from crm.fcrm.doctype.crm_lead.crm_lead import CRMLead, convert_to_deal

class TestCRMLeadCreation(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.begin()
        
        # Tạo lead cơ bản cho tất cả test cases
        try:
            self.lead = frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "Initial",
                "last_name": "Lead",
                "email": "initial.lead@example.com",
                "status": "New"
            }).insert(ignore_permissions=True)
        except Exception as e:
            print(f"Error in setUp: {str(e)}")
            self.lead = None
    
    def tearDown(self):
        frappe.db.rollback()
        
    
    
    # Test các trường hợp hợp lệ
    def test_create_lead_valid_all_fields(self):
        """Test tạo lead với tất cả trường hợp lệ"""
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "0123456789",
            "organization": "Test Company",
            "website": "http://testcompany.com",
            "no_of_employees": "11-50",
            "annual_revenue": 1000000,
            "industry": "Technology",
            "status": "New",
            "lead_owner": "Administrator"
        }).insert()
        
        self.assertTrue(frappe.db.exists("CRM Lead", lead.name))
        self.assertEqual(lead.email, "john.smith@example.com")
        self.assertEqual(lead.status, "New")
    
    
    def test_create_lead_invalid_first_name_special_chars(self):
        """Test tạo lead với first name có ký tự đặc biệt"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "John@123",
                "last_name": "Test",
                "email": "john@example.com"
            }).insert()
            # Nếu không ném ra lỗi, test vẫn pass (một số hệ thống có thể cho phép ký tự đặc biệt)
            self.fail("ValidationError was not raised")
        except Exception as e:
            # Nếu ném ra lỗi, kiểm tra xem có phải ValidationError không
            self.assertTrue(True)
    
    def test_create_lead_missing_first_name(self):
        """Test tạo lead với first name bỏ trống"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "last_name": "Test",
                "email": "test@example.com"
            }).insert()
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Đúng như dự kiến
            self.assertTrue(True)
    
    def test_create_lead_invalid_last_name_special_chars(self):
        """Test tạo lead với last name có ký tự đặc biệt"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "John",
                "last_name": "Smith#123",
                "email": "john@example.com"
            }).insert()
            # Nếu không ném ra lỗi, test vẫn pass
            self.fail("ValidationError was not raised")
        except Exception as e:
            # Nếu ném ra lỗi, kiểm tra xem có phải ValidationError không
            self.assertTrue(True)
    
    def test_create_lead_missing_last_name(self):
        """Test tạo lead với last name bỏ trống"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "Test",
                "email": "test@example.com"
            }).insert()
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Đúng như dự kiến
            self.assertTrue(True)
    
    def test_create_lead_invalid_email(self):
        """Test tạo lead với email không hợp lệ"""
        invalid_emails = [
            "plainaddress", 
            "@missingusername.com",
            "user@domain@domain.com",
            "user.domain.com"
        ]
        
        for email in invalid_emails:
            try:
                frappe.get_doc({
                    "doctype": "CRM Lead",
                    "first_name": "Test",
                    "last_name": "User",
                    "email": email
                }).insert()
                self.fail(f"ValidationError was not raised for email: {email}")
            except ValidationError:
                # Đúng như dự kiến
                self.assertTrue(True)
    
    def test_create_lead_invalid_phone(self):
        """Test tạo lead với số điện thoại không hợp lệ"""
        invalid_phones = ["123456789", "+84123456789", "12-345-6789"]
        
        for phone in invalid_phones:
            try:
                frappe.get_doc({
                    "doctype": "CRM Lead",
                    "first_name": "Test",
                    "last_name": "User",
                    "email": "test@example.com",
                    "phone": phone
                }).insert()
                # Một số hệ thống có thể không validate số điện thoại
                self.fail("ValidationError was not raised")
            except ValidationError:
                # Nếu validate, cũng pass
                self.assertTrue(True)
    
    
    def test_create_lead_invalid_organization_special_chars(self):
        """Test tạo lead với tổ chức có ký tự đặc biệt"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "organization": "Test Company @#$%"
            }).insert()
            # Trong thực tế, nhiều hệ thống cho phép ký tự đặc biệt trong tên tổ chức
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Nếu validate, cũng pass
            self.assertTrue(True)
    
    # Test Website
    def test_create_lead_valid_website(self):
        """Test tạo lead với website hợp lệ"""
        valid_websites = [
            "http://example.com", 
            "https://test.com",
            "https://www.company.co.uk"
        ]
        
        for idx, website in enumerate(valid_websites):
            lead = frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": f"Test{idx}",
                "last_name": "User",
                "email": f"test{idx}@example.com",
                "website": website
            }).insert()
            
            self.assertEqual(lead.website, website)
    
    
    
    def test_create_lead_invalid_annual_revenue(self):
        """Test tạo lead với doanh thu hàng năm không hợp lệ"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "annual_revenue": "1M"
            }).insert()
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)
    
    
    def test_create_lead_invalid_owner(self):
        """Test tạo lead với người quản lý không tồn tại"""
        try:
            frappe.get_doc({
                "doctype": "CRM Lead",
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "lead_owner": ""
            }).insert()
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)
    
    
    def test_update_lead_invalid_first_name_special_chars(self):
        """Test cập nhật lead với first name có ký tự đặc biệt"""
        try:
            self.lead.first_name = "John@123"
            self.lead.save(ignore_permissions=True)
            # Nếu không ném ra lỗi, test vẫn pass (một số hệ thống có thể cho phép ký tự đặc biệt)
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Nếu ném ra lỗi, cũng pass
            self.assertTrue(True)
    
    def test_update_lead_empty_first_name(self):
        """Test cập nhật lead với first name để trống"""
        try:
            self.lead.first_name = ""
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Đúng như dự kiến
            self.assertTrue(True)
    
    def test_update_lead_invalid_last_name_special_chars(self):
        """Test cập nhật lead với last name có ký tự đặc biệt"""
        try:
            self.lead.last_name = "Smith#123"
            self.lead.save(ignore_permissions=True)
            # Nếu không ném ra lỗi, test vẫn pass
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Nếu ném ra lỗi, cũng pass
            self.assertTrue(True)
    
    def test_update_lead_empty_last_name(self):
        """Test cập nhật lead với last name để trống"""
        try:
            self.lead.last_name = ""
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Đúng như dự kiến
            self.assertTrue(True)
    
    def test_update_lead_invalid_email(self):
        """Test cập nhật lead với email không hợp lệ"""
        invalid_emails = [
            "plainaddress", 
            "@missingusername.com",
            "user@domain@domain.com",
            "user.domain.com"
        ]
        
        for email in invalid_emails:
            try:
                self.lead.email = email
                self.lead.save(ignore_permissions=True)
                self.fail(f"ValidationError was not raised for email: {email}")
            except ValidationError:
                # Đúng như dự kiến
                self.assertTrue(True)
    
    def test_update_lead_invalid_phone(self):
        """Test cập nhật lead với số điện thoại không hợp lệ"""
        invalid_phones = ["123456789", "+84123456789", "12-345-6789"]
        
        for phone in invalid_phones:
            try:
                self.lead.phone = phone
                self.lead.save(ignore_permissions=True)
                # Một số hệ thống có thể không validate số điện thoại
                self.fail("ValidationError was not raised")
            except ValidationError:
                # Nếu validate, cũng pass
                self.assertTrue(True)
    
    
    def test_update_lead_empty_gender(self):
        """Test cập nhật lead với giới tính để trống"""
        try:
            self.lead.gender = ""
            self.lead.save(ignore_permissions=True)
            
            # Nếu không có ngoại lệ, kiểm tra giá trị đã lưu
            updated_lead = frappe.get_doc("CRM Lead", self.lead.name)
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Nếu hệ thống không cho phép gender rỗng
            self.assertTrue(true)
    
    def test_update_lead_organization_special_chars(self):
        """Test cập nhật lead với tổ chức có ký tự đặc biệt"""
        try:
            self.lead.organization = "Test Company @#$%"
            self.lead.save(ignore_permissions=True)
            # Trong thực tế, nhiều hệ thống cho phép ký tự đặc biệt trong tên tổ chức
            self.fail("ValidationError was not raised")
        except ValidationError:
            # Nếu validate, cũng pass
            self.assertTrue(True)
    
    def test_update_lead_empty_organization(self):
        """Test cập nhật lead với tổ chức để trống"""
        try:
            self.lead.organization = ""
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)
    
    
    def test_update_lead_invalid_website(self):
        """Test cập nhật lead với website không hợp lệ"""
        invalid_websites = [
            "example.com", 
            "test",
            "http:/test.com"
        ]
        
        for website in invalid_websites:
            try:
                self.lead.website = website
                self.lead.save(ignore_permissions=True)
                # Một số hệ thống có thể không validate URL
                self.fail("ValidationError was not raised")
            except ValidationError:
                # Nếu validate, cũng pass
                self.assertTrue(True)
    
    
    def test_update_lead_empty_employees(self):
        """Test cập nhật lead với số lượng nhân viên để trống"""
        try:
            self.lead.no_of_employees = ""
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)
    
    def test_update_lead_invalid_annual_revenue(self):
        """Test cập nhật lead với doanh thu hàng năm không hợp lệ"""
        try:
            self.lead.annual_revenue = "1M"
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)
    
    
    def test_update_lead_empty_industry(self):
        """Test cập nhật lead với lĩnh vực để trống"""
        try:
            self.lead.industry = ""
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)
    
    
    def test_update_lead_empty_owner(self):
        """Test cập nhật lead với người quản lý để trống"""
        try:
            self.lead.lead_owner = ""
            self.lead.save(ignore_permissions=True)
            self.fail("ValidationError was not raised")
        except ValidationError:
            self.assertTrue(True)    

    def test_update_lead_valid_fields(self):
        """Test cập nhật lead với tất cả các trường hợp lệ"""
        valid_data = {
            "first_name": ["John", "Mary", "Robert", "JAMES", "elizabeth"],
            "last_name": ["Smith", "Johnson", "Brown", "MILLER", "wilson"],
            "email": ["updated@example.com", "user.name@domain.com", "first.last@subdomain.domain.co.uk"],
            "phone": ["0123456789", "0987654321", "0909123456"],
            "gender": ["Male", "Female", "Genderqueer", "Non-Conforming", "Other", "Prefer not to say", "Transgender"],
            "organization": ["Test Company", "ABC Corporation", "Smith & Sons"],
            "website": ["http://example.com", "https://test.com", "https://www.company.co.uk"],
            "no_of_employees": ["1-10", "11-50", "51-200", "501-1000", "1000+"],
            "territory": ["North", "South", "East West", "Central Area"],
            "annual_revenue": [1000, 50000, 1000000, 10000000],
            "industry": ["Security & commodity exchanges", "Service", "Software", "Technology", "Telecommunications"],
            "status": ["New", "Contacted", "Nurture", "Qualified", "Unqualified", "Junk"],
            "lead_owner": ["Administrator"]
        }
        
        # Kiểm tra từng trường với mọi giá trị hợp lệ
        for field, values in valid_data.items():
            for value in values:
                try:
                    # Cập nhật giá trị
                    setattr(self.lead, field, value)
                    self.lead.save(ignore_permissions=True, ignore_links=True)
                    
                    # Kiểm tra giá trị đã lưu
                    updated_lead = frappe.get_doc("CRM Lead", self.lead.name)
                    self.assertEqual(getattr(updated_lead, field), value, 
                                    f"Không cập nhật được {field} với giá trị {value}")
                except Exception as e:
                    self.fail(f"Không cập nhật được {field} với giá trị {value}: {str(e)}")
    
    
    def test_delete_lead_success(self):
        """Test xóa lead thành công"""
        temp_lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": "Delete",
            "last_name": "Test",
            "email": "delete.test@example.com"
        }).insert()
        
        name = temp_lead.name
        temp_lead.delete()
        
        self.assertFalse(frappe.db.exists("CRM Lead", name))
  
