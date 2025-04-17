from frappe.tests.utils import FrappeTestCase
import frappe


class TestCRMOrganization(FrappeTestCase):
    def setUp(self):
        # Được gọi trước mỗi test case
        frappe.db.commit()  # Đảm bảo trạng thái DB sạch trước khi chạy test

    def tearDown(self):
        # Được gọi sau mỗi test case
        frappe.db.rollback()  # Rollback tất cả các thay đổi trong cơ sở dữ liệu

    # Org-01: Tạo CRM Organization hợp lệ
    # Kiểm tra việc tạo tổ chức với đầy đủ thông tin hợp lệ
    def test_create_valid_organization(self):
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Test Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)

        # Lấy lại tổ chức vừa tạo
        saved_organization = frappe.get_doc("CRM Organization", organization.name)

        # Kiểm tra các trường
        self.assertEqual(saved_organization.organization_name, "Test Organization")
        self.assertEqual(saved_organization.address, "123 Test Street")
        self.assertEqual(saved_organization.website, "https://example.com")
        self.assertEqual(saved_organization.annual_revenue, 11)
        self.assertEqual(saved_organization.industry, "Software")
        self.assertEqual(saved_organization.no_of_employees, "11-50")

    # Org-02: Tạo CRM Organization thiếu trường bắt buộc
    # Kiểm tra việc tạo tổ chức mà thiếu trường bắt buộc (organization_name)
    def test_create_organization_missing_required_fields(self):
        # Check xem có trả về frappe.ValidationError không
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "CRM Organization",
                # Thiếu trường organization_name
                "address": "123 Test Street",
                "website": "https://example.com",
                "annual_revenue": 11,
                "industry": "Software",
                "no_of_employees": "11-50"
            }).insert(ignore_permissions=True)

	# Org-03: Tạo CRM Organization với URL website không hợp lệ
	# Kiểm tra việc tạo tổ chức với URL website không hợp lệ nhưng vẫn được lưu vào cơ sở dữ liệu
    def test_create_organization_with_invalid_website(self):
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Invalid Website Organization",
            "address": "123 Test Street",
            "website": "invalid-url",  # URL không hợp lệ
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)

        # Lấy lại tổ chức vừa tạo
        saved_organization = frappe.get_doc("CRM Organization", organization.name)

        # Kiểm tra các trường
        self.assertEqual(saved_organization.organization_name, "Invalid Website Organization")
        self.assertEqual(saved_organization.address, "123 Test Street")
        self.assertEqual(saved_organization.website, "invalid-url")  # URL không hợp lệ vẫn được lưu
        self.assertEqual(saved_organization.annual_revenue, 11)
        self.assertEqual(saved_organization.industry, "Software")
        self.assertEqual(saved_organization.no_of_employees, "11-50")

    # Org-04: Tạo CRM Organization với tên tổ chức trùng lặp
    # Kiểm tra việc tạo tổ chức với tên tổ chức đã tồn tại
    def test_create_organization_with_duplicate_name(self):
        # Tạo tổ chức đầu tiên
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Duplicate Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)

        # Tạo tổ chức thứ hai với cùng tên
        with self.assertRaises(frappe.DuplicateEntryError):
            frappe.get_doc({
                "doctype": "CRM Organization",
                "organization_name": "Duplicate Organization",  # Tên trùng lặp
                "address": "123 Test Street",
                "website": "https://example.com",
                "annual_revenue": 11,
                "industry": "Software",
                "no_of_employees": "11-50"
            }).insert(ignore_permissions=True)

    # Org-05: Tạo CRM Organization với số lượng nhân viên không hợp lệ
    # Kiểm tra việc tạo tổ chức với số lượng nhân viên không hợp lệ
    def test_create_organization_with_invalid_no_of_employees(self):
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "CRM Organization",
                "organization_name": "Invalid Employees Organization",
                "address": "123 Test Street",
                "website": "https://example.com",
                "annual_revenue": 11,
                "industry": "Software",
                "no_of_employees": "invalid-range"  # Giá trị không hợp lệ
            }).insert(ignore_permissions=True)
            
	# Org-06: Tạo CRM Organization với các trường trống (trừ organization_name)
	# Kiểm tra việc tạo tổ chức với các trường khác để trống
    def test_create_organization_with_empty_fields(self):
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Empty Fields Organization"  # Chỉ có organization_name
        }).insert(ignore_permissions=True)
    
        # Lấy lại tổ chức vừa tạo
        saved_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertEqual(saved_organization.organization_name, "Empty Fields Organization")
        self.assertIsNone(saved_organization.address)  # Trường address trống
        self.assertIsNone(saved_organization.website)  # Trường website trống
        self.assertEqual(saved_organization.annual_revenue, 0.0)  # Trường annual_revenue mặc định là 0.0
        self.assertIsNone(saved_organization.industry)  # Trường industry trống
        self.assertEqual(saved_organization.no_of_employees, "1-10")  # Trường no_of_employees trống 
        
    # Org-07: Tạo CRM Organization với SQL Injection
	# Kiểm tra việc tạo tổ chức với chuỗi SQL Injection
    def test_create_organization_with_sql_injection(self):
        sql_injection_string = "'; DROP TABLE `tabCRM Organization`; --"
    
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": sql_injection_string,
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lấy lại tổ chức vừa tạo
        saved_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertEqual(saved_organization.organization_name, sql_injection_string)
        self.assertEqual(saved_organization.address, "123 Test Street")
        self.assertEqual(saved_organization.website, "https://example.com")
        self.assertEqual(saved_organization.annual_revenue, 11)
        self.assertEqual(saved_organization.industry, "Software")
        self.assertEqual(saved_organization.no_of_employees, "11-50")
        
    # Org-08: Tạo CRM Organization với HTML trong các trường
	# Kiểm tra việc tạo tổ chức với HTML trong các trường
    def test_create_organization_with_html_in_fields(self):
        html_string = "<script>alert(1)</script>"
    
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": html_string,
            "address": html_string,
            "website": html_string,
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lấy lại tổ chức vừa tạo
        saved_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertEqual(saved_organization.organization_name, html_string)
        self.assertEqual(saved_organization.address, html_string)
        self.assertEqual(saved_organization.website, html_string)
        self.assertEqual(saved_organization.annual_revenue, 11)
        self.assertEqual(saved_organization.industry, "Software")
        self.assertEqual(saved_organization.no_of_employees, "11-50")
        
    # Org-09: Chỉnh sửa CRM Organization với thông tin hợp lệ
	# Kiểm tra việc chỉnh sửa tổ chức với thông tin hợp lệ
    def test_update_organization_with_valid_data(self):
        # Tạo tổ chức ban đầu
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Original Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Cập nhật thông tin tổ chức
        organization.organization_name = "Updated Organization"
        organization.address = "123 Test Street"
        organization.website = "https://updated-example.com"
        organization.annual_revenue = 20
        organization.industry = "Sports"
        organization.no_of_employees = "51-200"
        organization.save(ignore_permissions=True)
    
        # Lấy lại tổ chức đã chỉnh sửa
        updated_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertEqual(updated_organization.organization_name, "Updated Organization")
        self.assertEqual(updated_organization.address, "123 Test Street")
        self.assertEqual(updated_organization.website, "https://updated-example.com")
        self.assertEqual(updated_organization.annual_revenue, 20)
        self.assertEqual(updated_organization.industry, "Sports")
        self.assertEqual(updated_organization.no_of_employees, "51-100")
	
	# Org-10: Chỉnh sửa CRM Organization với SQL Injection
	# Kiểm tra việc chỉnh sửa tổ chức với chuỗi SQL Injection
    def test_update_organization_with_sql_injection(self):
        # Tạo tổ chức ban đầu
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Original Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Cập nhật thông tin tổ chức với SQL Injection
        sql_injection_string = "'; DROP TABLE `tabCRM Organization`; --"
        organization.organization_name = sql_injection_string
        organization.save(ignore_permissions=True)
    
        # Lấy lại tổ chức đã chỉnh sửa
        updated_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertEqual(updated_organization.organization_name, sql_injection_string)
	
	# Org-11: Chỉnh sửa CRM Organization với HTML trong các trường
	# Kiểm tra việc chỉnh sửa tổ chức với HTML trong các trường
    def test_update_organization_with_html_in_fields(self):
        # Tạo tổ chức ban đầu
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Original Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Cập nhật thông tin tổ chức với HTML
        html_string = "<script>alert(1)</script>"
        organization.organization_name = html_string
        organization.address = html_string
        organization.website = html_string
        organization.save(ignore_permissions=True)
    
        # Lấy lại tổ chức đã chỉnh sửa
        updated_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertEqual(updated_organization.organization_name, html_string)
        self.assertEqual(updated_organization.address, html_string)
        self.assertEqual(updated_organization.website, html_string)
	
	# Org-12: Chỉnh sửa CRM Organization với các trường trống
	# Kiểm tra việc chỉnh sửa tổ chức với các trường khác để trống
    def test_update_organization_with_empty_fields(self):
        # Tạo tổ chức ban đầu
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Original Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Cập nhật thông tin tổ chức với các trường trống
        organization.address = None
        organization.website = None
        organization.industry = None
        organization.no_of_employees = None
        organization.save(ignore_permissions=True)
    
        # Lấy lại tổ chức đã chỉnh sửa
        updated_organization = frappe.get_doc("CRM Organization", organization.name)
    
        # Kiểm tra các trường
        self.assertIsNone(updated_organization.address)
        self.assertIsNone(updated_organization.website)
        self.assertEqual(updated_organization.annual_revenue, 11)  # Không thay đổi
        self.assertIsNone(updated_organization.industry)
        self.assertIsNone(updated_organization.no_of_employees)
        
        
    # Org-13: Lọc CRM Organization theo organization_name
	# Kiểm tra việc lọc tổ chức theo organization_name
    def test_filter_organization_by_name(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Filter Test Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lọc theo organization_name
        results = frappe.get_list(
            "CRM Organization",
            filters={"organization_name": ["like", "%Filter Test%"]},
            fields=["name", "organization_name"]
        )
    
        # Kiểm tra kết quả
        for result in results:
            self.assertIn("Filter Test", result["organization_name"])
	
	# Org-14: Lọc CRM Organization theo address
	# Kiểm tra việc lọc tổ chức theo address
    def test_filter_organization_by_address(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Address Filter Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lọc theo address
        results = frappe.get_list(
            "CRM Organization",
            filters={"address": ["like", "%Street%"]},
            fields=["name", "address"]
        )
    
        # Kiểm tra kết quả
        for result in results:
            self.assertIn("Street", result["address"])
	
	# Org-15: Lọc CRM Organization theo website
	# Kiểm tra việc lọc tổ chức theo website
    def test_filter_organization_by_website(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Website Filter Organization",
            "address": "123 Test Street",
            "website": "https://filter-example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lọc theo website
        results = frappe.get_list(
            "CRM Organization",
            filters={"website": ["like", "%filter-example.com%"]},
            fields=["name", "website"]
        )
    
        # Kiểm tra kết quả
        for result in results:
            self.assertIn("filter-example.com", result["website"])
	
	# Org-16: Lọc CRM Organization theo annual_revenue
	# Kiểm tra việc lọc tổ chức theo annual_revenue
    def test_filter_organization_by_annual_revenue(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Revenue Filter Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 50,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lọc theo annual_revenue
        results = frappe.get_list(
            "CRM Organization",
            filters={"annual_revenue": 50},
            fields=["name", "annual_revenue"]
        )
    
        # Kiểm tra kết quả
        for result in results:
            self.assertEqual(result["annual_revenue"], 50)
	
	# Org-17: Lọc CRM Organization theo industry
	# Kiểm tra việc lọc tổ chức theo industry
    def test_filter_organization_by_industry(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Industry Filter Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Health Care",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Lọc theo industry
        results = frappe.get_list(
            "CRM Organization",
            filters={"industry": ["like", "%Health Care%"]},
            fields=["name", "industry"]
        )
    
        # Kiểm tra kết quả
        for result in results:
            self.assertIn("Health Care", result["industry"])
	
	# Org-18: Lọc CRM Organization theo no_of_employees
	# Kiểm tra việc lọc tổ chức theo no_of_employees
    def test_filter_organization_by_no_of_employees(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Employees Filter Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "51-200"
        }).insert(ignore_permissions=True)
    
        # Lọc theo no_of_employees
        results = frappe.get_list(
            "CRM Organization",
            filters={"no_of_employees": ["like", "%51-200%"]},
            fields=["name", "no_of_employees"]
        )
    
        # Kiểm tra kết quả
        for result in results:
            self.assertIn("51-200", result["no_of_employees"])
            
    # Org-19: Chỉnh sửa CRM Organization với tên tổ chức trùng lặp
	# Kiểm tra việc chỉnh sửa tổ chức với tên tổ chức đã tồn tại
    def test_update_organization_with_duplicate_name(self):
        # Tạo tổ chức đầu tiên
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Original Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Tạo tổ chức thứ hai
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Duplicate Organization",
            "address": "456 Test Street",
            "website": "https://example2.com",
            "annual_revenue": 20,
            "industry": "Healthcare",
            "no_of_employees": "51-100"
        }).insert(ignore_permissions=True)
    
        # Cập nhật tên tổ chức thứ hai trùng với tổ chức đầu tiên
        organization.organization_name = "Original Organization"
        with self.assertRaises(frappe.DuplicateEntryError):
            organization.save(ignore_permissions=True)
            
    # Org-20: Xóa CRM Organization
	# Kiểm tra việc xóa tổ chức
    def test_delete_organization(self):
        # Tạo tổ chức
        organization = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Delete Test Organization",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 11,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        # Xóa tổ chức
        frappe.delete_doc("CRM Organization", organization.name, ignore_permissions=True)
    
        # Kiểm tra tổ chức đã bị xóa
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.get_doc("CRM Organization", organization.name)
            
    # Org-21: Sắp xếp CRM Organization theo organization_name
	# Kiểm tra việc sắp xếp tổ chức theo organization_name
    def test_sort_organization_by_name(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "B Organization"
        }).insert(ignore_permissions=True)
    
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "A Organization"
        }).insert(ignore_permissions=True)
    
        # Lấy danh sách tổ chức sắp xếp theo organization_name tăng dần
        results = frappe.get_list(
            "CRM Organization",
            fields=["organization_name"],
            order_by="organization_name asc"
        )
    
        # Kiểm tra kết quả
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["organization_name"], results[i + 1]["organization_name"])
	
	
	# Org-22: Sắp xếp CRM Organization theo no_of_employees
	# Kiểm tra việc sắp xếp tổ chức theo no_of_employees
    def test_sort_organization_by_no_of_employees(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "no_of_employees": "11-50"
        }).insert(ignore_permissions=True)
    
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "no_of_employees": "51-100"
        }).insert(ignore_permissions=True)
    
        # Lấy danh sách tổ chức sắp xếp theo no_of_employees tăng dần
        results = frappe.get_list(
            "CRM Organization",
            fields=["no_of_employees"],
            order_by="no_of_employees asc"
        )
    
        # Kiểm tra kết quả
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["no_of_employees"], results[i + 1]["no_of_employees"])
	
	
	# Org-23: Sắp xếp CRM Organization theo currency
	# Kiểm tra việc sắp xếp tổ chức theo currency
    def test_sort_organization_by_currency(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "currency": "USD"
        }).insert(ignore_permissions=True)
    
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "currency": "EUR"
        }).insert(ignore_permissions=True)
    
        # Lấy danh sách tổ chức sắp xếp theo currency tăng dần
        results = frappe.get_list(
            "CRM Organization",
            fields=["currency"],
            order_by="currency asc"
        )
    
        # Kiểm tra kết quả
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["currency"], results[i + 1]["currency"])
	
	
	# Org-24: Sắp xếp CRM Organization theo annual_revenue
	# Kiểm tra việc sắp xếp tổ chức theo annual_revenue
    def test_sort_organization_by_annual_revenue(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "annual_revenue": 10
        }).insert(ignore_permissions=True)
    
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "annual_revenue": 50
        }).insert(ignore_permissions=True)
    
        # Lấy danh sách tổ chức sắp xếp theo annual_revenue tăng dần
        results = frappe.get_list(
            "CRM Organization",
            fields=["annual_revenue"],
            order_by="annual_revenue asc"
        )
    
        # Kiểm tra kết quả
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["annual_revenue"], results[i + 1]["annual_revenue"])
	
	
	# Org-25: Sắp xếp CRM Organization theo website
	# Kiểm tra việc sắp xếp tổ chức theo website
    def test_sort_organization_by_website(self):
        # Tạo tổ chức
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "website": "https://b-example.com"
        }).insert(ignore_permissions=True)
    
        frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "website": "https://a-example.com"
        }).insert(ignore_permissions=True)
    
        # Lấy danh sách tổ chức sắp xếp theo website tăng dần
        results = frappe.get_list(
            "CRM Organization",
            fields=["website"],
            order_by="website asc"
        )
    
        # Kiểm tra kết quả
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["website"], results[i + 1]["website"])