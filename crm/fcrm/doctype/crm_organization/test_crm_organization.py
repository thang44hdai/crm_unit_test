from frappe.tests.utils import FrappeTestCase
import frappe
from crm.fcrm.doctype.crm_organization.crm_organization import CRMOrganization
from datetime import datetime, timedelta

class TestCRMOrganization(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.begin()

    def tearDown(self):
        frappe.db.rollback()

    # Org-01: Tạo CRM Organization hợp lệ
    def test_create_valid_organization(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "hahaha",
            "address": "123 Test Street",
            "website": "https://example.com",
            "annual_revenue": 100,
            "industry": "Software",
            "no_of_employees": "11-50"
        }).insert()
        saved_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(saved_org.organization_name, "hahaha")
        self.assertEqual(saved_org.address, "123 Test Street")
        self.assertEqual(saved_org.website, "https://example.com")
        self.assertEqual(saved_org.annual_revenue, 100)
        self.assertEqual(saved_org.industry, "Software")
        self.assertEqual(saved_org.no_of_employees, "11-50")
        now = datetime.now()
        creation_time = saved_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-02: Tạo CRM Organization thiếu trường bắt buộc
    def test_create_organization_missing_required_fields(self):
        with self.assertRaises(frappe.ValidationError):
            CRMOrganization({
                "doctype": "CRM Organization",
                # Thiếu organization_name
                "address": "123 Test Street"
            }).insert()

    # Org-03: Tạo CRM Organization với các trường set cứng với giá trị không đúng
    def test_create_organization_with_invalid_website(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Invalid Website Org",
            "website": "invalid-url"
        }).insert()
        saved_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(saved_org.website, "invalid-url")
        now = datetime.now()
        creation_time = saved_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-04: Tạo CRM Organization với tên trùng lặp
    def test_create_organization_with_duplicate_name(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Dup Org"
        }).insert()
        with self.assertRaises(frappe.DuplicateEntryError):
            CRMOrganization({
                "doctype": "CRM Organization",
                "organization_name": "Dup Org"
            }).insert()

    # Org-05: Tạo CRM Organization với số lượng nhân viên không hợp lệ
    def test_create_organization_with_invalid_no_of_employees(self):
        with self.assertRaises(frappe.ValidationError):
            CRMOrganization({
                "doctype": "CRM Organization",
                "organization_name": "Invalid Employees Org",
                "no_of_employees": "invalid"
            }).insert()

    # Org-06: Tạo CRM Organization với các trường trống (trừ organization_name)
    def test_create_organization_with_empty_fields(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Empty Org"
        }).insert()
        saved_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(saved_org.organization_name, "Empty Org")
        self.assertFalse(saved_org.address)
        self.assertFalse(saved_org.website)
        now = datetime.now()
        creation_time = saved_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))


    # Org-07: Tạo CRM Organization với SQL Injection
    def test_create_organization_with_sql_injection(self):
        sql_injection = "'; DROP TABLE `tabCRM Organization`; --"
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": sql_injection
        }).insert()
        saved_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(saved_org.organization_name, sql_injection)
        now = datetime.now()
        creation_time = saved_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-08: Tạo CRM Organization với HTML trong các trường
    def test_create_organization_with_html_in_fields(self):
        html = "<script>alert(1)</script>"
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": html,
            "address": "123 Test Street",
        }).insert()
        saved_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(saved_org.organization_name, html)
        now = datetime.now()
        creation_time = saved_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-09: Chỉnh sửa CRM Organization với thông tin hợp lệ
    def test_update_organization_with_valid_data(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Original Org"
        }).insert()
        org.organization_name = "Updated Org"
        org.save()
        updated_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(updated_org.organization_name, "Updated Org")
        now = datetime.now()
        creation_time = updated_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-10: Chỉnh sửa CRM Organization với SQL Injection
    def test_update_organization_with_sql_injection(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Original Org"
        }).insert()
        sql_injection = "'; DROP TABLE `tabCRM Organization`; --"
        org.organization_name = sql_injection
        org.save()
        updated_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(updated_org.organization_name, sql_injection)
        now = datetime.now()
        creation_time = updated_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-11: Chỉnh sửa CRM Organization với HTML trong các trường
    def test_update_organization_with_html_in_fields(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Original Org"
        }).insert()
        html = "<script>alert(1)</script>"
        org.organization_name = html
        org.save()
        updated_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(updated_org.organization_name, html)
        now = datetime.now()
        creation_time = updated_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))

    # Org-12: Chỉnh sửa CRM Organization với các trường trống
    def test_update_organization_with_empty_fields(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Original Org",
            "address": "123 Test Street"
        }).insert()
        org.address = ""
        org.save()
        updated_org = frappe.get_doc("CRM Organization", org.name)
        self.assertFalse(updated_org.address)
        now = datetime.now()
        creation_time = updated_org.creation.replace(tzinfo=None)
        self.assertTrue(now - creation_time < timedelta(minutes=1))
        
    # Org-13: Lọc CRM Organization theo organization_name
    def test_filter_organization_by_name(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Filter Org"
        }).insert()
        results = frappe.get_list("CRM Organization", filters={"organization_name": ["like", "%Filter%"]}, fields=["organization_name"])
        self.assertTrue(any("Filter" in org["organization_name"] for org in results))

    # Org-14: Lọc CRM Organization theo address
    def test_filter_organization_by_address(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Address Org",
            "address": "123 Test Street"
        }).insert()
        results = frappe.get_list("CRM Organization", filters={"address": ["like", "%Test St%"]}, fields=["address"])
        self.assertTrue(any("Test St" in org["address"] for org in results))

    # Org-15: Lọc CRM Organization theo website
    def test_filter_organization_by_website(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Website Org",
            "website": "https://filter-example.com"
        }).insert()
        results = frappe.get_list("CRM Organization", filters={"website": ["like", "%filter-example.com%"]}, fields=["website"])
        self.assertTrue(any("filter-example.com" in org["website"] for org in results))

    # Org-16: Lọc CRM Organization theo annual_revenue
    def test_filter_organization_by_annual_revenue(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Revenue Org",
            "annual_revenue": 50
        }).insert()
        results = frappe.get_list("CRM Organization", filters={"annual_revenue": 50}, fields=["annual_revenue"])
        self.assertTrue(any(org["annual_revenue"] == 50 for org in results))

    # Org-17: Lọc CRM Organization theo industry
    def test_filter_organization_by_industry(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Industry Org",
            "industry": "Health Care"
        }).insert()
        results = frappe.get_list("CRM Organization", filters={"industry": ["like", "%Health Care%"]}, fields=["industry"])
        self.assertTrue(any("Health Care" in org["industry"] for org in results))

    # Org-18: Lọc CRM Organization theo no_of_employees
    def test_filter_organization_by_no_of_employees(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Employees Org",
            "no_of_employees": "51-200"
        }).insert()
        results = frappe.get_list("CRM Organization", filters={"no_of_employees": ["like", "%51-200%"]}, fields=["no_of_employees"])
        self.assertTrue(any("51-200" in org["no_of_employees"] for org in results))

    # Org-19: Chỉnh sửa CRM Organization với tên tổ chức trùng lặp
    def test_update_organization_with_duplicate_name(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Original Org"
        }).insert()
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Dup Org"
        }).insert()
        org.organization_name = "Original Org"
        try:
            org.save()
        except Exception:
            pass  # Có thể raise ValidationError hoặc không
        # Reload lại từ DB để kiểm tra tên không bị đổi thành trùng
        org.reload()
        self.assertNotEqual(org.organization_name, "Original Org") 

    # Org-20: Xóa CRM Organization
    def test_delete_organization(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Delete Org"
        }).insert()
        org_name = org.name
        org.delete()
        self.assertFalse(frappe.db.exists("CRM Organization", org_name))

    # Org-21: Sắp xếp CRM Organization theo organization_name
    def test_sort_organization_by_name(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "B Org"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "A Org"
        }).insert()
        results = frappe.get_list("CRM Organization", fields=["organization_name"], order_by="organization_name asc")
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["organization_name"], results[i + 1]["organization_name"])

    # Org-22: Sắp xếp CRM Organization theo no_of_employees
    def test_sort_organization_by_no_of_employees(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "no_of_employees": "11-50"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "no_of_employees": "51-200"
        }).insert()
        results = frappe.get_list("CRM Organization", fields=["no_of_employees"], order_by="no_of_employees asc")
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["no_of_employees"], results[i + 1]["no_of_employees"])

    # Org-23: Sắp xếp CRM Organization theo currency
    def test_sort_organization_by_currency(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "currency": "USD"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "currency": "EUR"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 3"
            # Không truyền currency, sẽ là None
        }).insert()
        results = frappe.get_list("CRM Organization", fields=["currency"], order_by="currency asc")
        # Nếu currency là None thì gán ""
        currencies = [r["currency"] if r["currency"] is not None else "" for r in results]
        for i in range(len(currencies) - 1):
            self.assertLessEqual(currencies[i], currencies[i + 1])
            
    # Org-24: Sắp xếp CRM Organization theo annual_revenue
    def test_sort_organization_by_annual_revenue(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "annual_revenue": 10
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "annual_revenue": 50
        }).insert()
        results = frappe.get_list("CRM Organization", fields=["annual_revenue"], order_by="annual_revenue asc")
        for i in range(len(results) - 1):
            self.assertLessEqual(results[i]["annual_revenue"], results[i + 1]["annual_revenue"])

    # Org-25: Sắp xếp CRM Organization theo website
    def test_sort_organization_by_website(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 1",
            "website": "https://b-example.com"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 2",
            "website": "https://a-example.com"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 3"
            # Không truyền website, sẽ là None
        }).insert()
        results = frappe.get_list("CRM Organization", fields=["website"], order_by="website asc")
        # Nếu website là None thì gán ""
        websites = [r["website"] if r["website"] is not None else "" for r in results]
        for i in range(len(websites) - 1):
            self.assertLessEqual(websites[i], websites[i + 1])
            
    # Org-26: Tạo CRM Organization với tên tổ chức lớn hơn 255 ký tự
    def test_create_organization_with_long_name(self):
        long_name = "A" * 256
        try:
            CRMOrganization({
                "doctype": "CRM Organization",
                "organization_name": long_name
            }).insert()
        except Exception:
            pass  # Có thể raise ValidationError hoặc không
        # Đảm bảo không có bản ghi nào được lưu với tên này
        exists = frappe.db.exists("CRM Organization", {"organization_name": long_name})
        self.assertFalse(exists)
        
    # Org-27: Chỉnh sửa CRM Organization với tên tổ chức chứa ký tự đặc biệt
    def test_update_organization_with_special_characters(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Normal Org"
        }).insert()
        special_name = "!@#$%^&*()_+|~=`{}[]:\";'<>?,./"
        org.organization_name = special_name
        org.save()
        updated_org = frappe.get_doc("CRM Organization", org.name)
        self.assertEqual(updated_org.organization_name, special_name)
        
        # Org-28: Chỉnh sửa CRM Organization với tên tổ chức rỗng
    def test_update_organization_with_empty_name(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Normal Org"
        }).insert()
        org.organization_name = ""
        try:
            org.save()
        except Exception:
            pass  # Có thể raise ValidationError hoặc không
        # Reload lại từ DB để kiểm tra tên không bị đổi thành rỗng
        org.reload()
        self.assertNotEqual(org.organization_name, "")
        
        # Org-29: Lọc CRM Organization theo currency chứa ký tự nhập
    def test_filter_organization_by_currency(self):
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Currency Org",
            "currency": "VND"
        }).insert()
        CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Other Org",
            "currency": "USD"
        }).insert()
        results = frappe.get_list(
            "CRM Organization",
            filters={"currency": ["like", "%VN%"]},
            fields=["organization_name", "currency"]
        )
        self.assertTrue(any("VN" in (org["currency"] or "") for org in results))

    # Org-30: Lọc CRM Organization theo ngày tạo (creation)
    def test_filter_organization_by_creation(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Created Today"
        }).insert()
        # org.creation là string, cần chuyển sang datetime
        creation_dt = datetime.strptime(org.creation, "%Y-%m-%d %H:%M:%S.%f")
        today = creation_dt.strftime("%Y-%m-%d")
        results = frappe.get_list(
            "CRM Organization",
            filters={"creation": ["like", f"{today}%"]},
            fields=["name", "creation"]
        )
        self.assertTrue(any(r["name"] == org.name for r in results))
        
    # Org-31: Lọc CRM Organization theo người sửa gần nhất (Last Updated By)
    def test_filter_organization_by_last_updated_by(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Modified Org"
        }).insert()
        org.organization_name = "Modified Org Updated"
        org.save()
        # Trường last_updated_by thường là 'modified_by' trong Frappe
        results = frappe.get_list(
            "CRM Organization",
            filters={"modified_by": org.modified_by},
            fields=["name", "modified_by"]
        )
        self.assertTrue(any(r["name"] == org.name for r in results))
        
    # Org-32: Lọc CRM Organization với nhiều trường cùng lúc
    def test_filter_organization_by_multiple_fields(self):
        org = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Multi Org",
            "currency": "VND",
            "industry": "Software"
        }).insert()
        results = frappe.get_list(
            "CRM Organization",
            filters={
                "organization_name": "Multi Org",
                "currency": "VND",
                "industry": "Software"
            },
            fields=["name", "organization_name", "currency", "industry"]
        )
        self.assertTrue(any(
            r["name"] == org.name and r["currency"] == "VND" and r["industry"] == "Software"
            for r in results
        ))
    
        # Org-33: Xóa nhiều CRM Organization cùng lúc
    def test_delete_multiple_organizations(self):
        org1 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Delete Org 1"
        }).insert()
        org2 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Delete Org 2"
        }).insert()
        org3 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Delete Org 3"
        }).insert()
        names = [org1.name, org2.name, org3.name]
        for name in names:
            frappe.delete_doc("CRM Organization", name)
        for name in names:
            self.assertFalse(frappe.db.exists("CRM Organization", name))
            
        # Org-34: Sắp xếp CRM Organization theo người sửa gần nhất (Last Updated By)
    def test_sort_organization_by_last_updated_by(self):
        org1 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 1"
        }).insert()
        org2 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 2"
        }).insert()
        # Cập nhật org2 để modified_by là user hiện tại
        org2.organization_name = "Org 2 Updated"
        org2.save()
        results = frappe.get_list(
            "CRM Organization",
            fields=["name", "modified_by"],
            order_by="modified_by asc"
        )
        modified_bys = [r["modified_by"] if r["modified_by"] is not None else "" for r in results]
        for i in range(len(modified_bys) - 1):
            self.assertLessEqual(modified_bys[i], modified_bys[i + 1])

    # Org-35: Sắp xếp CRM Organization theo ngày tạo (Created On)
    def test_sort_organization_by_creation(self):
        org1 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 1"
        }).insert()
        org2 = CRMOrganization({
            "doctype": "CRM Organization",
            "organization_name": "Org 2"
        }).insert()
        results = frappe.get_list(
            "CRM Organization",
            fields=["name", "creation"],
            order_by="creation asc"
        )
        creation_dates = [r["creation"] if r["creation"] is not None else "" for r in results]
        for i in range(len(creation_dates) - 1):
            self.assertLessEqual(creation_dates[i], creation_dates[i + 1])