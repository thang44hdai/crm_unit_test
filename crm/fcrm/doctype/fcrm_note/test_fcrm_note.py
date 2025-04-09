from frappe.tests.utils import FrappeTestCase
import frappe

class TestFCRMNote(FrappeTestCase):    
    def setUp(self):
        super().setUp()
        # Tạo user test nếu chưa có, không gửi email chào mừng
        # Thiết lập môi trường cần thiết cho test, đảm bảo trạng thái ban đầu sạch sẽ và nhất quán.
        if not frappe.db.exists("User", "test-user@example.com"):
            frappe.get_doc({
                "doctype": "User",
                "email": "test-user@example.com",
                "first_name": "Test User",
                "roles": [{"role": "System Manager"}],
                "send_welcome_email": 0  # Tránh gửi email
            }).insert(ignore_permissions=True)

        # Đảm bảo Email Account "_Test Email Account 1" được cấu hình đúng
        frappe.db.set_value("Email Account", "_Test Email Account 1", {
            "enable_outgoing": 1,
            "default_outgoing": 1,
            "smtp_server": "localhost",
            "email_id": "test@example.com"
        })
        frappe.db.commit()

    def test_create_fcrm_note(self):
        # Tạo một FCRM Note mới
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "test 9/4",
            "content": "<p>hello</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
 
        # frappe.db.commit()
        
        # Lấy lại note vừa tạo
        saved_note = frappe.get_doc("FCRM Note", note.name)

        # Kiểm tra các trường
        self.assertEqual(saved_note.title, "test 9/4")
        self.assertEqual(saved_note.content, "<p>hello</p>")
        self.assertEqual(saved_note.reference_doctype, "CRM Lead")
        self.assertEqual(saved_note.reference_docname, "CRM-LEAD-2025-00001")
        self.assertEqual(saved_note.owner, "Administrator")