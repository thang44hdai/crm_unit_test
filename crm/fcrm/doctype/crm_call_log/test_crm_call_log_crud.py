# Copyright (c) 2025, Frappe Technologies Pvt. Ltd.
# See license.txt

from frappe.tests import IntegrationTestCase
import frappe
from frappe import ValidationError

class TestCRUDCallLog(IntegrationTestCase):
    """
    Integration tests for CRUD operations on CRM Call Log.
    """

    def setUp(self):
        super().setUp()
        # Xóa hết bản ghi cũ để đảm bảo môi trường sạch
        for rec in frappe.get_all('CRM Call Log'):
            frappe.delete_doc('CRM Call Log', rec.name, force=True)

    def test_create_call_log_valid_TC_CRUD_CALLLOG_001(self):
        """
        TC_CRUD_CALLLOG_001: Tạo Call Log với dữ liệu hợp lệ.
        """
        call = frappe.new_doc('CRM Call Log')
        # Cần gán id bắt buộc do naming rule
        call.id = 'CALLLOG-001'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 60
        call.set('from', '+841234567')
        call.to = '+849876543'
        call.insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists('CRM Call Log', call.name))
        frappe.delete_doc('CRM Call Log', call.name, force=True)

    def test_create_call_log_sql_injection_from_TC_CRUD_CALLLOG_002(self):
        """
        TC_CRUD_CALLLOG_002: Tạo Call Log với SQL Injection ở trường 'from'.
        """
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-002'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 30
        call.set('from', "'; DROP TABLE `tabUser`; --")
        call.to = '+849876543'
        with self.assertRaises(ValidationError):
            call.insert(ignore_permissions=True)

    def test_create_call_log_html_injection_recording_url_TC_CRUD_CALLLOG_003(self):
        """
        TC_CRUD_CALLLOG_003: Tạo Call Log với script HTML trong recording_url.
        """
        malicious = '<script>alert("xss")</script>'
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-003'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 45
        call.set('from', '+841234567')
        call.to = '+849876543'
        call.recording_url = malicious
        call.insert(ignore_permissions=True)
        fetched = frappe.get_doc('CRM Call Log', call.name)
        self.assertNotIn('<script>', fetched.recording_url)
        frappe.delete_doc('CRM Call Log', call.name, force=True)

    def test_create_call_log_exceed_length_recording_url_TC_CRUD_CALLLOG_004(self):
        """
        TC_CRUD_CALLLOG_004: Tạo Call Log với recording_url vượt giới hạn 255 ký tự.
        """
        long_data = 'A' * 300
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-004'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 50
        call.set('from', '+841234567')
        call.to = '+849876543'
        call.recording_url = long_data
        with self.assertRaises(ValidationError):
            call.insert(ignore_permissions=True)

    def test_read_call_log_exists_TC_CRUD_CALLLOG_005(self):
        """
        TC_CRUD_CALLLOG_005: Đọc Call Log tồn tại.
        """
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-005'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 10
        call.set('from', '+841111111')
        call.to = '+842222222'
        call.insert(ignore_permissions=True)
        fetched = frappe.get_doc('CRM Call Log', call.name)
        self.assertEqual(fetched.name, call.name)
        frappe.delete_doc('CRM Call Log', call.name, force=True)

    def test_read_call_log_not_exists_TC_CRUD_CALLLOG_006(self):
        """
        TC_CRUD_CALLLOG_006: Đọc Call Log không tồn tại.
        """
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.get_doc('CRM Call Log', 'INVALID_NAME')

    def test_update_call_log_valid_status_TC_CRUD_CALLLOG_007(self):
        """
        TC_CRUD_CALLLOG_007: Cập nhật status hợp lệ (chọn 'Busy').
        """
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-007'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 20
        call.set('from', '+843333333')
        call.to = '+844444444'
        call.insert(ignore_permissions=True)
        # Cập nhật status thành giá trị hợp lệ
        call.status = 'Busy'
        call.save(ignore_permissions=True)
        updated = frappe.get_doc('CRM Call Log', call.name)
        self.assertEqual(updated.status, 'Busy')
        frappe.delete_doc('CRM Call Log', call.name, force=True)

    def test_update_call_log_sql_injection_from_TC_CRUD_CALLLOG_008(self):
        """
        TC_CRUD_CALLLOG_008: Cập nhật trường 'from' với SQL Injection.
        """
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-008'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 25
        call.set('from', '+843333333')
        call.to = '+846666666'
        call.insert(ignore_permissions=True)
        call.set('from', "'; DROP TABLE `tabUser`; --")
        with self.assertRaises(ValidationError):
            call.save(ignore_permissions=True)
        frappe.delete_doc('CRM Call Log', call.name, force=True)

    def test_update_call_log_html_status_TC_CRUD_CALLLOG_009(self):
        """
        TC_CRUD_CALLLOG_009: Cập nhật status chứa HTML, phải lỗi ValidationError.
        """
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-009'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 30
        call.set('from', '+847777777')
        call.to = '+848888888'
        call.insert(ignore_permissions=True)
        call.status = '<b>Bold</b>'
        with self.assertRaises(ValidationError):
            call.save(ignore_permissions=True)

    def test_delete_call_log_exists_TC_CRUD_CALLLOG_010(self):
        """
        TC_CRUD_CALLLOG_010: Xóa Call Log tồn tại.
        """
        call = frappe.new_doc('CRM Call Log')
        call.id = 'CALLLOG-010'
        call.type = 'Incoming'
        call.status = 'Completed'
        call.duration = 15
        call.set('from', '+849999999')
        call.to = '+841010101'
        call.insert(ignore_permissions=True)
        frappe.delete_doc('CRM Call Log', call.name, force=True)
        self.assertFalse(frappe.db.exists('CRM Call Log', call.name))

    def test_delete_call_log_not_exists_TC_CRUD_CALLLOG_011(self):
        """
        TC_CRUD_CALLLOG_011: Xóa Call Log không tồn tại.
        """
        # Không raise exception, chỉ assert không tồn tại
        frappe.delete_doc('CRM Call Log', 'DOES_NOT_EXIST', force=True)
        self.assertFalse(frappe.db.exists('CRM Call Log', 'DOES_NOT_EXIST'))