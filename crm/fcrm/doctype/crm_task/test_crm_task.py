import frappe
from frappe.tests.utils import FrappeTestCase
import unittest
from unittest.mock import patch
from pymysql.err import OperationalError
from crm.fcrm.doctype.crm_task.crm_task import CRMTask

class TestCRMTaskFull(FrappeTestCase):

    def setUp(self):
        """Chuẩn bị: đảm bảo đang dùng Administrator và clean DB."""
        super().setUp()
        frappe.set_user("Administrator")
        self.user = "Administrator"

    def tearDown(self):
        """Rollback DB sau mỗi test để tách biệt dữ liệu."""
        frappe.db.rollback()

    def create_task(self, **fields):
        """
        Helper: tạo và insert một CRM Task với các trường tùy chọn.
        Trả về document vừa tạo.
        """
        data = {
            "doctype": "CRM Task",
            "title": "Sample Task",
            "status": "Todo"
        }
        data.update(fields)
        task = frappe.get_doc(data)
        task.insert(ignore_permissions=True)
        frappe.db.commit()
        return task

    # --- 1. Create ---
    def test_task_create_valid(self):
        """TC_TASK_001: Tạo Task với đủ trường bắt buộc"""
        task = self.create_task(
            title="CRUD Test Insert",
            status="Todo",
            assigned_to=self.user,
            due_date="2025-12-31",
            priority="High"
        )
        self.assertTrue(frappe.db.exists("CRM Task", task.name),
                        "Task mới phải được lưu thành công")

    def test_task_create_missing_title(self):
        """TC_TASK_002: Tạo Task khi title để trống """
        with self.assertRaises(frappe.MandatoryError):
            self.create_task(
                title="",
                priority="High",
                assigned_to=self.user,
                status="Todo"
            )

    def test_task_create_invalid_due_date_format(self):
        """TC_TASK_003: Tạo Task với due_date sai định dạng"""
        with self.assertRaises(OperationalError):
            self.create_task(due_date="not-a-date")

    def test_task_create_past_due_date(self):
        """TC_TASK_004: Tạo Task với due_date trong quá khứ"""
        with self.assertRaises(frappe.ValidationError):
            self.create_task(due_date="2025-04-10")

    # --- 2. Read ---
    def test_get_existing_task(self):
        """TC_TASK_005: Lấy Task tồn tại theo name"""
        task = self.create_task()
        fetched = frappe.get_doc("CRM Task", task.name)
        self.assertEqual(fetched.name, task.name)

    def test_get_nonexistent_task(self):
        """TC_TASK_006: Lấy Task không tồn tại"""
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.get_doc("CRM Task", "does-not-exist")

    # --- 3. Update ---
    def test_update_status_todo_to_done(self):
        """TC_TASK_007: Cập nhật status 'Todo' → 'Done' → thành công."""
        task = self.create_task(status="Todo")
        task.status = "Done"
        task.save(ignore_permissions=True)
        frappe.db.commit()
        updated = frappe.get_doc("CRM Task", task.name)
        self.assertEqual(updated.status, "Done")

    def test_update_multiple_fields(self):
        """TC_TASK_008: Cập nhật đồng thời status và priority → thành công."""
        task = self.create_task(status="Todo", priority="Low")
        task.status = "In Progress"
        task.priority = "High"
        task.save(ignore_permissions=True)
        frappe.db.commit()
        updated = frappe.get_doc("CRM Task", task.name)
        self.assertEqual(updated.status, "In Progress")
        self.assertEqual(updated.priority, "High")

    def test_update_no_change(self):
        """TC_TASK_009: Lưu Task không thay đổi thông tin"""
        task = self.create_task(title="No Change")
        original_mod = frappe.get_value("CRM Task", task.name, "modified")
        task.save(ignore_permissions=True)
        frappe.db.commit()
        self.assertEqual(original_mod,
                         frappe.get_value("CRM Task", task.name, "modified"))

    def test_update_invalid_due_date(self):
        """TC_TASK_010: Cập nhật due_date sai định dạng"""
        task = self.create_task()
        task.due_date = "bad-format"
        with self.assertRaises(OperationalError):
            task.save(ignore_permissions=True)

    def test_update_past_due_date(self):
        """TC_TASK_011: Cập nhật due_date quá khứ"""
        task = self.create_task()
        task.due_date = "2025-04-10"
        with self.assertRaises(frappe.ValidationError):
            task.save(ignore_permissions=True)

    # --- 4. Delete ---
    def test_delete_existing_task(self):
        """TC_TASK_012: Xóa Task tồn tại"""
        task = self.create_task()
        name = task.name
        task.delete(ignore_permissions=True)
        frappe.db.commit()
        self.assertFalse(frappe.db.exists("CRM Task", name))

    def test_delete_nonexistent_task(self):
        """TC_TASK_013: Xóa Task không tồn tại """
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.delete_doc("CRM Task", "no-such-task", force=True)

    # --- 5. Hooks & Assignment ---
    def test_after_insert_assign_to(self):
        """TC_TASK_014: Thêm Task mới với assigned_to → gọi assign()."""
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            self.create_task(assigned_to=self.user)
            mock_assign.assert_called_once()

    def test_after_insert_no_assign(self):
        """TC_TASK_015: Thêm Task mới không có assigned_to → không gọi assign()."""
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            self.create_task(assigned_to="")
            mock_assign.assert_not_called()

    def test_assign_to_valid(self):
        """TC_TASK_016: Thêm Task mới với assigned_to → gọi assign()."""
        task = self.create_task(assigned_to=self.user)
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            task.assign_to()
            mock_assign.assert_called_once()

    def test_assign_to_skip(self):
        """TC_TASK_017: Thêm mới công việc có gán người thực hiện là rỗng → không gọi assign()."""
        task = self.create_task(assigned_to="")
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            task.assign_to()
            mock_assign.assert_not_called()

    def test_unassign_from_previous_user(self):
        """TC_TASK_018: Huỷ bỏ người thực hiện cũ khi gán người thực hiện mới."""
        task = self.create_task(assigned_to=self.user)
        with patch("crm.fcrm.doctype.crm_task.crm_task.unassign") as mock_unassign:
            task.unassign_from_previous_user(self.user)
            mock_unassign.assert_called_once_with("CRM Task", task.name, self.user)

    def test_validate_change_assignment(self):
        """TC_TASK_019: Thay đổi người thực hiện trong validate() → gọi assign() và unassign()."""
        task = self.create_task(assigned_to=self.user)
        old = type("OldDoc", (), {"assigned_to": self.user})
        with patch.object(task, "get_doc_before_save", return_value=old):
            with patch("crm.fcrm.doctype.crm_task.crm_task.unassign") as mock_unassign, \
                 patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
                task.assigned_to = "Guest"
                task.validate()
                mock_unassign.assert_called_once()
                mock_assign.assert_called_once()

    def test_validate_skip_for_new_or_unassigned(self):
        """TC_TASK_020: Không thay đổi người thực hiện trong validate() nếu là Task mới hoặc không có người thực hiện."""
        new_task = frappe.new_doc("CRM Task")
        new_task.title = "New"
        new_task.assigned_to = None
        with patch.object(new_task, "assign_to") as mock_assign, \
             patch.object(new_task, "unassign_from_previous_user") as mock_unassign:
            new_task.validate()
            mock_assign.assert_not_called()
            mock_unassign.assert_not_called()

    # --- 6. View Configurations ---
    def test_default_list_data(self):
        """TC_TASK_021: Lấy cấu hình mặc định cho danh sách Task."""
        data = CRMTask.default_list_data()
        self.assertIn("columns", data)
        self.assertIn("rows", data)
        labels = [c.get("label") for c in data["columns"]]
        for label in ("Title", "Status", "Due Date"):
            self.assertIn(label, labels)

    def test_default_kanban_settings(self):
        """TC_TASK_022: Lấy cấu hình mặc định cho Kanban."""
        settings = CRMTask.default_kanban_settings()
        for key in ("column_field", "title_field", "kanban_fields"):
            self.assertIn(key, settings)


if __name__ == "__main__":
    unittest.main()
