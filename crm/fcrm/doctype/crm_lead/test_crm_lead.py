import frappe
from frappe.tests import UnitTestCase, IntegrationTestCase
from unittest.mock import patch, MagicMock
from frappe import PermissionError, ValidationError
from types import SimpleNamespace

from crm.fcrm.doctype.crm_lead.api import get_lead
from crm.fcrm.doctype.crm_lead.crm_lead import CRMLead, convert_to_deal

# # ==============================
# # Unit tests cho API get_lead
# # ==============================
# class TestCRMLeadAPI(UnitTestCase):

#     def test_get_lead_success_TC_LEAD_API_001(self):
#         """
#         TC_LEAD_API_001: get_lead trả về dict bao gồm fields_meta, _form_script và _assign
#         """
#         # 1. Tạo fake_doc có .name và .as_dict()
#         fake_doc = SimpleNamespace(
#             name='LEAD-1',
#             as_dict=lambda: frappe._dict({'name': 'LEAD-1'})
#         )

#         # 2. Patch các hàm dependency trong api module
#         with patch('crm.fcrm.doctype.crm_lead.api.frappe.get_doc', return_value=fake_doc), \
#              patch('crm.fcrm.doctype.crm_lead.api.get_fields_meta', return_value={'meta': 'fields'}), \
#              patch('crm.fcrm.doctype.crm_lead.api.get_form_script', return_value='script'), \
#              patch('crm.fcrm.doctype.crm_lead.api.get_assigned_users', return_value=['u1', 'u2']):
            
#             result = get_lead('LEAD-1')

#         # 3. Kiểm tra kết quả
#         self.assertIsInstance(result, dict)
#         self.assertEqual(result['fields_meta'], {'meta': 'fields'})
#         self.assertEqual(result['_form_script'], 'script')
#         self.assertEqual(result['_assign'], ['u1', 'u2'])

#     def test_get_lead_permission_error_TC_LEAD_API_002(self):
#         """
#         TC_LEAD_API_002: get_lead phải báo lỗi PermissionError khi thiếu quyền đọc
#         """
#         fake_doc = MagicMock()
#         fake_doc.check_permission.side_effect = PermissionError

#         with patch('crm.fcrm.doctype.crm_lead.api.frappe.get_doc', return_value=fake_doc):
#             with self.assertRaises(PermissionError):
#                 get_lead('LEAD-2')


# ==============================
# Unit tests cho model CRMLead
# ==============================
class TestCRMLeadModel(UnitTestCase):
    def setUp(self):
        # Khởi tạo một CRM Lead và bỏ qua mandatory
        self.lead = frappe.new_doc('CRM Lead')
        self.lead.flags.ignore_mandatory = True

    def test_set_full_name_TC_LEAD_001(self):
        """TC_LEAD_001: set_full_name phải ghép salutation, first, middle, last đúng thứ tự"""
        self.lead.salutation = 'Mr.'
        self.lead.first_name = 'John'
        self.lead.middle_name = 'Q.'
        self.lead.last_name = 'Public'
        self.lead.set_full_name()
        self.assertEqual(self.lead.lead_name, 'Mr. John Q. Public')

    def test_set_lead_name_missing_data_error_TC_LEAD_002(self):
        """TC_LEAD_002: set_lead_name phải báo lỗi khi không có name/org/email"""
        self.lead.lead_name = ''
        self.lead.organization = ''
        self.lead.email = ''
        self.lead.flags.ignore_mandatory = False
        with self.assertRaises(ValidationError):
            self.lead.set_lead_name()

    def test_set_lead_name_use_organization_TC_LEAD_003(self):
        """TC_LEAD_003: set_lead_name dùng organization khi có giá trị"""
        self.lead.lead_name = ''
        self.lead.organization = 'Acme'
        self.lead.set_lead_name()
        self.assertEqual(self.lead.lead_name, 'Acme')

    def test_set_lead_name_use_email_prefix_TC_LEAD_004(self):
        """TC_LEAD_004: set_lead_name lấy tiền tố email khi không có organization"""
        self.lead.lead_name = ''
        self.lead.organization = ''
        self.lead.email = 'alice@example.com'
        self.lead.set_lead_name()
        self.assertEqual(self.lead.lead_name, 'alice')

    def test_set_title_priority_organization_TC_LEAD_005(self):
        """TC_LEAD_005: set_title ưu tiên organization rồi lead_name"""
        self.lead.lead_name = 'LeadName'
        self.lead.organization = ''
        self.lead.set_title()
        self.assertEqual(self.lead.title, 'LeadName')
        self.lead.organization = 'OrgX'
        self.lead.set_title()
        self.assertEqual(self.lead.title, 'OrgX')

    @patch('crm.fcrm.doctype.crm_lead.crm_lead.has_gravatar', return_value='img.png')
    def test_validate_email_assigns_image_TC_LEAD_006(self, mock_gravatar):
        """TC_LEAD_006: validate_email gán image từ has_gravatar nếu email hợp lệ"""
        self.lead.email = 'user@example.com'
        self.lead.flags.ignore_email_validation = False
        self.lead.validate_email()
        self.assertEqual(self.lead.image, 'img.png')

    @patch('crm.fcrm.doctype.crm_lead.crm_lead.validate_email_address')
    def test_validate_email_same_owner_error_TC_LEAD_007(self, mock_validate):
        """TC_LEAD_007: validate_email phải báo lỗi khi email trùng lead_owner"""
        self.lead.email = 'user@example.com'
        self.lead.lead_owner = 'user@example.com'
        self.lead.flags.ignore_email_validation = False
        with self.assertRaises(ValidationError):
            self.lead.validate_email()

    @patch('frappe.share.add_docshare')
    @patch('frappe.share.remove')
    def test_share_with_agent_add_and_remove_docshare_TC_LEAD_008(self, mock_remove, mock_add):
        """TC_LEAD_008: share_with_agent thêm docshare mới và xóa docshare cũ"""
        # Trả về list các obj có .user
        fake_shares = [frappe._dict({'name':'s1','user':'old'})]
        with patch('crm.fcrm.doctype.crm_lead.crm_lead.frappe.get_all', return_value=fake_shares), \
             patch('crm.fcrm.doctype.crm_lead.crm_lead.frappe.db.exists', side_effect=[False, True]):

            self.lead.name = 'LEAD-1'
            self.lead.doctype = 'CRM Lead'
            self.lead.share_with_agent('new_agent')

            mock_add.assert_called_with(
                'CRM Lead', 'LEAD-1', 'new_agent',
                write=1, flags={'ignore_share_permission': True}
            )
            mock_remove.assert_called_with('CRM Lead', 'LEAD-1', 'old')

    def test_convert_to_deal_no_permission_error_TC_LEAD_009(self):
        """TC_LEAD_009: convert_to_deal phải báo lỗi PermissionError khi thiếu quyền write"""
        with patch('crm.fcrm.doctype.crm_lead.crm_lead.frappe.has_permission', return_value=False):
            with self.assertRaises(PermissionError):
                convert_to_deal(lead='LEAD-1')


# ==============================
# Integration tests cho CRUD CRM Lead
# ==============================
class IntegrationTestCRMLead(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        # Xóa toàn bộ Lead trước khi test
        for rec in frappe.get_all('CRM Lead'):
            frappe.delete_doc('CRM Lead', rec.name, force=True)

    def tearDown(self):
        # Rollback lần cuối
        for rec in frappe.get_all('CRM Lead'):
            frappe.delete_doc('CRM Lead', rec.name, force=True)

    def test_create_lead_valid_TC_LEAD_CRUD_010(self):
        """TC_LEAD_CRUD_010: Tạo CRM Lead với các trường bắt buộc thành công"""
        lead = frappe.new_doc('CRM Lead')
        lead.naming_series = 'CRM-LEAD-.YYYY.-'
        lead.first_name = 'Test'
        lead.insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists('CRM Lead', lead.name))

    def test_read_lead_exists_TC_LEAD_CRUD_011(self):
        """TC_LEAD_CRUD_011: Đọc CRM Lead tồn tại thành công"""
        lead = frappe.new_doc('CRM Lead')
        lead.naming_series = 'CRM-LEAD-.YYYY.-'
        lead.first_name = 'Read'
        lead.insert(ignore_permissions=True)
        fetched = frappe.get_doc('CRM Lead', lead.name)
        self.assertEqual(fetched.name, lead.name)

    def test_read_lead_not_exists_TC_LEAD_CRUD_012(self):
        """TC_LEAD_CRUD_012: Đọc CRM Lead không tồn tại phải báo lỗi DoesNotExistError"""
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.get_doc('CRM Lead', 'INVALID')

    def test_update_lead_valid_email_TC_LEAD_CRUD_013(self):
        """TC_LEAD_CRUD_013: Cập nhật email hợp lệ thành công"""
        lead = frappe.new_doc('CRM Lead')
        lead.naming_series = 'CRM-LEAD-.YYYY.-'
        lead.first_name = 'Upd'
        lead.email = 'old@example.com'
        lead.insert(ignore_permissions=True)

        lead.email = 'new@example.com'
        lead.save(ignore_permissions=True)
        updated = frappe.get_doc('CRM Lead', lead.name)
        self.assertEqual(updated.email, 'new@example.com')

    def test_update_lead_sql_injection_email_TC_LEAD_CRUD_014(self):
        """TC_LEAD_CRUD_014: Cập nhật email chứa SQL injection phải báo lỗi ValidationError"""
        lead = frappe.new_doc('CRM Lead')
        lead.naming_series = 'CRM-LEAD-.YYYY.-'
        lead.first_name = 'SQL'
        lead.email = 'v@x.com'
        lead.insert(ignore_permissions=True)

        lead.email = "'; DROP TABLE `tabUser`; --"
        with self.assertRaises(ValidationError):
            lead.save(ignore_permissions=True)

    def test_delete_lead_exists_TC_LEAD_CRUD_015(self):
        """TC_LEAD_CRUD_015: Xóa CRM Lead đã tồn tại thành công"""
        lead = frappe.new_doc('CRM Lead')
        lead.naming_series = 'CRM-LEAD-.YYYY.-'
        lead.first_name = 'Del'
        lead.insert(ignore_permissions=True)

        frappe.delete_doc('CRM Lead', lead.name, force=True)
        self.assertFalse(frappe.db.exists('CRM Lead', lead.name))

    def test_delete_lead_not_exists_TC_LEAD_CRUD_016(self):
        """TC_LEAD_CRUD_016: Xóa CRM Lead không tồn tại không gây lỗi"""
        frappe.delete_doc('CRM Lead', 'DOES_NOT_EXIST', force=True)
        self.assertFalse(frappe.db.exists('CRM Lead', 'DOES_NOT_EXIST'))
