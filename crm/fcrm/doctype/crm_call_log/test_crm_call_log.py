import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch
from pymysql.err import OperationalError, DataError
from crm.fcrm.doctype.crm_call_log.crm_call_log import (
    CRMCallLog,
    parse_call_log,
    get_call_log,
    create_lead_from_call_log
)


class TestCRMCallLog(FrappeTestCase):

    def setUp(self):
        """Tạo dữ liệu mẫu: NOTE-001, TASK-001, LEAD-001, DEAL-001, CL-001"""
        super().setUp()
        frappe.set_user("Administrator")

        # FCRM Note
        if not frappe.db.exists("FCRM Note", "NOTE-001"):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "name": "NOTE-001",
                "title": "Ghi chú mẫu"
            }).insert(ignore_permissions=True)

        # CRM Task
        if not frappe.db.exists("CRM Task", "TASK-001"):
            frappe.get_doc({
                "doctype": "CRM Task",
                "name": "TASK-001",
                "title": "Task mẫu",
                "status": "Todo"
            }).insert(ignore_permissions=True)

        # CRM Lead
        if not frappe.db.exists("CRM Lead", "LEAD-001"):
            frappe.get_doc({
                "doctype": "CRM Lead",
                "name": "LEAD-001",
                "first_name": "Lead mẫu"
            }).insert(ignore_permissions=True)

        # CRM Deal
        if not frappe.db.exists("CRM Deal", "DEAL-001"):
            frappe.get_doc({
                "doctype": "CRM Deal",
                "name": "DEAL-001",
                "deal_name": "Deal mẫu"
            }).insert(ignore_permissions=True)

        # CRM Call Log mẫu
        if not frappe.db.exists("CRM Call Log", "CL-001"):
            frappe.get_doc({
                "doctype": "CRM Call Log",
                "id": "CL-001",
                "caller": "Administrator",
                "receiver": "Administrator",
                "type": "Incoming",
                "status": "Completed",
                "from": "0999",
                "to": "0123",
                "duration": 60
            }).insert(ignore_permissions=True)

        frappe.db.commit()

    def tearDown(self):
        """Rollback sau mỗi test để đảm bảo isolation."""
        frappe.db.rollback()

    # 1. Cấu hình List View mặc định
    def test_default_list_data(self):
        """TC_CALL_LOGS_001: Lấy cấu hình cột và dòng cho List View"""
        data = CRMCallLog.default_list_data()
        self.assertIn("columns", data)
        self.assertIn("rows", data)
        labels = [col["label"] for col in data["columns"]]
        for expected in ("Caller", "Receiver", "Duration"):
            self.assertIn(expected, labels)

    # 2. parse_list_data với danh sách rỗng
    def test_parse_list_data_empty(self):
        """TC_CALL_LOGS_002: Chuẩn hoá danh sách rỗng"""
        self.assertEqual(CRMCallLog.parse_list_data(None), [])

    # 3. parse_list_data với danh sách không rỗng
    def test_parse_list_data_non_empty(self):
        """TC_CALL_LOGS_003: Chuẩn hoá danh sách không rỗng"""
        sample = {"duration": 120, "type": "Incoming", "from": "0123", "receiver": "user@e"}
        with patch("crm.fcrm.doctype.crm_call_log.crm_call_log.parse_call_log", lambda c: {"ok": True}):
            result = CRMCallLog.parse_list_data([sample])
        self.assertEqual(result, [{"ok": True}])

    # 4. has_link() trả về True
    def test_has_link_true(self):
        """TC_CALL_LOGS_004: Kiểm tra liên kết với cuộc gọi hợp lệ"""
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.links = []
        cl.append("links", {
            "link_doctype": "CRM Task",
            "link_name": "TASK-001"
        })
        self.assertTrue(cl.has_link("CRM Task", "TASK-001"))

    # 5. has_link() trả về False
    def test_has_link_false(self):
        """TC_CALL_LOGS_005: Kiểm tra liên kết với cuộc gọi không có liên kết tương ứng"""
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.links = []
        self.assertFalse(cl.has_link("CRM Task", "TASK-001"))

    # 6. link_with_reference_doc() thêm link khi chưa có
    def test_link_with_reference_doc_add(self):
        """TC_CALL_LOGS_006: Thêm mới liên kết nếu chưa tồn tại"""
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.links = []
        cl.link_with_reference_doc("CRM Lead", "LEAD-001")
        # Check if the link was added by examining the child table items
        link_exists = False
        for link in cl.links:
            if link.link_doctype == "CRM Lead" and link.link_name == "LEAD-001":
                link_exists = True
                break
        self.assertTrue(link_exists)

    # 7. link_with_reference_doc() không duplicate
    def test_link_with_reference_doc_skip(self):
        """TC_CALL_LOGS_007: Không thêm mới liên kết nếu đã tồn tại"""
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.links = []
        cl.append("links", {
            "link_doctype": "CRM Lead",
            "link_name": "LEAD-001"
        })
        cl.link_with_reference_doc("CRM Lead", "LEAD-001")
        # Count the number of links with this specific link_name
        lead_links_count = 0
        for link in cl.links:
            if link.link_doctype == "CRM Lead" and link.link_name == "LEAD-001":
                lead_links_count += 1
        self.assertEqual(lead_links_count, 1)

    # 8. parse_call_log() cho Incoming
    @patch("crm.integrations.api.get_contact_by_phone_number",
           lambda num: {"full_name": "Nguyễn A", "image": "a.png"})
    @patch("frappe.db.get_values", lambda dt, n, f: [["Trần B", "b.png"]])
    def test_parse_call_log_incoming(self):
        """TC_CALL_LOGS_008: chuẩn hoá thông tin cuộc gọi đến"""
        inp = {"duration": 90, "type": "Incoming", "from": "0123", "receiver": "user"}
        out = parse_call_log(dict(inp))
        self.assertEqual(out["activity_type"], "incoming_call")
        self.assertEqual(out["_duration"], "00:01:30")
        self.assertEqual(out["_caller"]["label"], "Nguyễn A")
        self.assertEqual(out["_receiver"]["label"], "Trần B")
        self.assertFalse(out["show_recording"])

    # 9. parse_call_log() cho Outgoing
    @patch("crm.integrations.api.get_contact_by_phone_number",
           lambda num: {"full_name": "Phạm D", "image": "d.png"})
    @patch("frappe.db.get_values", lambda dt, n, f: [["Võ E", "e.png"]])
    def test_parse_call_log_outgoing(self):
        """TC_CALL_LOGS_009: Chuẩn hoá thông tin cuộc gọi đi"""
        inp = {"duration": 30, "type": "Outgoing", "to": "0456", "caller": "user"}
        out = parse_call_log(dict(inp))
        self.assertEqual(out["activity_type"], "outgoing_call")
        self.assertEqual(out["_duration"], "00:00:30")
        self.assertEqual(out["_receiver"]["label"], "Phạm D")
        self.assertEqual(out["_caller"]["label"], "Võ E")
        self.assertFalse(out["show_recording"])

    # 10. get_call_log() với note + reference CRM Lead
    def test_get_call_log_with_note_and_ref(self):
        """TC_CALL_LOGS_010: Lấy thông tin cuộc gọi với note và liên kết đến CRM Lead"""
        # Use mock to bypass link validation and document fetching
        with patch("frappe.model.document.Document._validate_links", return_value=None), \
             patch("frappe.get_cached_doc", side_effect=lambda *args, **kwargs: frappe._dict({
                "doctype": args[0],
                "name": args[1],
                "as_dict": lambda: {
                    "name": args[1], 
                    "note": "NOTE-001",
                    "reference_doctype": "CRM Lead",
                    "reference_docname": "LEAD-001"
                }
             })):
            
            # Test the function directly without saving a document
            out = get_call_log("CL-001")
            self.assertIn("NOTE-001", [n["name"] for n in out["_notes"]])
            self.assertEqual(out["_lead"], "LEAD-001")

    # 11. get_call_log() với links Task + Note
    def test_get_call_log_with_links_task_and_note(self):
        """TC_CALL_LOGS_011: Lấy thông tin cuộc gọi với liên kết đến Task và Note"""
        # Setup mocks for all function calls in the test
        with patch("frappe.model.document.Document._validate_links", return_value=None), \
             patch("frappe.get_cached_doc", side_effect=lambda *args, **kwargs: frappe._dict({
                 "doctype": args[0],
                 "name": args[1],
                 "as_dict": lambda: {"name": args[1], "title": f"Mock {args[0]}"},
                 "links": [
                     frappe._dict({"link_doctype": "CRM Task", "link_name": "TASK-001"}),
                     frappe._dict({"link_doctype": "FCRM Note", "link_name": "NOTE-001"})
                 ]
             })):
            
            # Test with mocked data
            out = get_call_log("CL-001")
            self.assertIn("TASK-001", [t["name"] for t in out["_tasks"]])
            self.assertIn("NOTE-001", [n["name"] for n in out["_notes"]])

    # 12. get_call_log() với name không tồn tại
    def test_get_call_log_invalid(self):
        """TC_CALL_LOGS_012: Lấy thông tin cuộc gọi với name không tồn tại"""
        with self.assertRaises(frappe.DoesNotExistError):
            get_call_log("NO-LOG")

    # 13. create_lead_from_call_log()
    def test_create_lead_from_call_log(self):
        """TC_CALL_LOGS_013: Tạo Lead từ Call Log và link lại"""
        lead_name = create_lead_from_call_log({"name": "CL-001", "from": "0999"})
        lead = frappe.get_doc("CRM Lead", lead_name)
        self.assertTrue(lead.first_name.startswith("Lead from call"))
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        self.assertTrue(cl.has_link("CRM Lead", lead_name))

    # 14. insert() hợp lệ
    def test_insert_call_log_valid(self):
        """TC_CALL_LOGS_014: Thêm mới cuộc gọi hợp lệ"""
        before = frappe.db.count("CRM Call Log")
        # Generate a unique ID with timestamp to avoid duplicate entries
        import datetime
        unique_id = f"CL-TEST-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cl = frappe.get_doc({
            "doctype": "CRM Call Log",
            "id": unique_id,           # Using a unique ID with timestamp
            "caller": "Administrator",
            "receiver": "Administrator",
            "type": "Incoming",
            "status": "Completed",
            "from": "0123",
            "to": "0456",
            "duration": 60
        })
        cl.insert(ignore_permissions=True)
        frappe.db.commit()
        after = frappe.db.count("CRM Call Log")
        self.assertEqual(after, before + 1)
        
        # Clean up the test document to avoid polluting the database
        frappe.delete_doc("CRM Call Log", unique_id, force=True)

    # 15. insert() thiếu from → MandatoryError
    def test_insert_call_log_missing_from(self):
        """TC_CALL_LOGS_015: Thêm mới cuộc gọi thiếu số gọi đi"""
        with self.assertRaises(frappe.MandatoryError):
            frappe.get_doc({
                "doctype": "CRM Call Log",
                "id": "CL-003",
                "caller": "Administrator",
                "receiver": "Administrator",
                "type": "Incoming",
                "status": "Completed",
                "from": "",              # Bỏ trống
                "to": "0456",
                "duration": 60
            }).insert(ignore_permissions=True)

    # 16. insert() thiếu to → MandatoryError
    def test_insert_call_log_missing_to(self):
        """TC_CALL_LOGS_016: Thêm mới cuộc gọi thiếu số gọi đến"""
        with self.assertRaises(frappe.MandatoryError):
            frappe.get_doc({
                "doctype": "CRM Call Log",
                "id": "CL-004",
                "caller": "Administrator",
                "receiver": "Administrator",
                "type": "Outgoing",
                "status": "Completed",
                "from": "0123",
                "to": "",               # Bỏ trống
                "duration": 60
            }).insert(ignore_permissions=True)

    # 17. insert() duration sai định dạng → ValidationError
    def test_insert_call_log_invalid_duration(self):
        """TC_CALL_LOGS_017: Thêm mới cuộc gọi với duration sai định dạng"""
        import datetime
        unique_id = f"CL-INVALID-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Tạo một document mới với duration sai định dạng
        doc = frappe.get_doc({
            "doctype": "CRM Call Log",
            "id": unique_id,
            "caller": "Administrator",
            "receiver": "Administrator", 
            "type": "Incoming",
            "status": "Completed",
            "from": "0123",
            "to": "0456",
            "duration": "60 phút"  # Sai định dạng
        })
                
        with self.assertRaises((frappe.ValidationError, DataError)):
            try:
                doc.insert(ignore_permissions=True)
            except Exception as e:
                if isinstance(e, DataError):
                    raise
                else:
                    raise

    # 18. save() cập nhật status
    def test_update_call_log_status(self):
        """TC_CALL_LOGS_018: Cập nhật status thành công"""
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.status = "Completed"
        cl.save(ignore_permissions=True)
        frappe.db.commit()
        self.assertEqual(frappe.get_value("CRM Call Log", "CL-001", "status"), "Completed")

    # 19. save() cập nhật type không hợp lệ
    def test_update_call_log_invalid_type(self):
        """TC_CALL_LOGS_019: Cập nhật type không hợp lệ """
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.type = "Unknown"
        with self.assertRaises(frappe.ValidationError):
            cl.save(ignore_permissions=True)

    # 20. delete() thành công
    def test_delete_call_log_valid(self):
        """TC_CALL_LOGS_020: Xoá cuộc gọi thành công"""
        before = frappe.db.count("CRM Call Log")
        cl = frappe.get_doc("CRM Call Log", "CL-001")
        cl.delete(ignore_permissions=True)
        frappe.db.commit()
        self.assertEqual(frappe.db.count("CRM Call Log"), before - 1)

    # 21. delete() không tồn tại → DoesNotExistError
    def test_delete_call_log_nonexistent(self):
        """TC_CALL_LOGS_021: Xoá cuộc gọi không tồn tại"""
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.delete_doc("CRM Call Log", "NO-LOG", force=True)


if __name__ == "__main__":
    unittest.main()
