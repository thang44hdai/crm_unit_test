# test_crm_task.py
from frappe.tests.utils import FrappeTestCase
import frappe
import unittest
from unittest.mock import patch
from crm.fcrm.doctype.crm_task.crm_task import CRMTask


class TestCRMTaskCRUD(FrappeTestCase):
    def setUp(self):
        super().setUp()
        # Sử dụng "Administrator" làm user mặc định (vì Administrator luôn tồn tại)
        self.test_user = "Administrator"
        # Tạo thêm các user cho việc test thay đổi assignment.
        for email in ["test-new@example.com"]:
            if not frappe.db.exists("User", email):
                frappe.get_doc({
                    "doctype": "User",
                    "email": email,
                    "first_name": email.split("@")[0],
                    "roles": [{"role": "Sales User"}],
                    "send_welcome_email": 0
                }).insert(ignore_permissions=True)
        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def create_crm_task(self, title="Unit Test Task", priority="High",
                        assigned_to=None, status="Todo",
                        extra_fields=None):
        """
        Helper: Tạo mới một CRM Task với dữ liệu cho trước.
        Input: Các trường bắt buộc và tùy chọn.
        Expected Output: Trả về một đối tượng CRMTask đã được insert vào DB.
        """
        if assigned_to is None:
            # Sử dụng user mặc định
            assigned_to = self.test_user

        data = {
            "doctype": "CRM Task",
            "title": title,
            "priority": priority,
            "assigned_to": assigned_to,
            "status": status,
        }
        if extra_fields:
            data.update(extra_fields)
        task = frappe.new_doc("CRM Task")
        for key, value in data.items():
            setattr(task, key, value)
        task.insert(ignore_permissions=True)
        frappe.db.commit()
        return task

    # ============================
    # 1. Test hàm after_insert()
    # ============================
    def test_after_insert_triggers_assign_to(self):
        """
        [TC-AI-001]
        Mục tiêu: Sau khi insert, assign_to() được gọi đúng một lần.
        """
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            # create_crm_task sẽ insert và tự động trigger after_insert
            self.create_crm_task()
            mock_assign.assert_called_once()

    def test_after_insert_no_assign_when_assigned_to_empty(self):
        """
        [TC-AI-002]
        Mục tiêu: Nếu assigned_to rỗng, không gọi assign.
        """
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            self.create_crm_task(assigned_to="")
            mock_assign.assert_not_called()

    def test_after_insert_invalid_assigned_to(self):
        """
        [TC-AI-003]
        Mục tiêu: Nếu assigned_to là user không tồn tại, khi insert Task sẽ raise LinkValidationError.
        """
        invalid_user = "nonexistent@example.com"
        # Đảm bảo user này không có trong DB
        if frappe.db.exists("User", invalid_user):
            frappe.delete_doc("User", invalid_user, force=True)
            frappe.db.commit()
        with self.assertRaises(frappe.LinkValidationError):
            self.create_crm_task(assigned_to=invalid_user)

    # ============================
    # 2. Test hàm validate()
    # ============================
    def test_validate_assignment_change(self):
        """
        [TC-V-001]
        Mục tiêu: Khi cập nhật Task và thay đổi assigned_to, validate() sẽ gọi unassign_from_previous_user() và assign_to().
        Input: Task ban đầu có assigned_to = "Administrator", sau đó thay đổi thành "test-new@example.com".
        Expected Output: Gọi unassign_from_previous_user("Administrator") và assign_to().
        Note: Sử dụng patch.object để override get_doc_before_save().
        """
        task = self.create_crm_task(assigned_to="Administrator")
        with patch.object(task, "get_doc_before_save", return_value=type("Dummy", (object,), {"assigned_to": "Administrator"})):
            with patch("crm.fcrm.doctype.crm_task.crm_task.unassign") as mock_unassign, \
                 patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
                task.assigned_to = "test-new@example.com"
                task.validate()
                mock_unassign.assert_called_once_with(task.doctype, task.name, "Administrator")
                mock_assign.assert_called_once()

    def test_validate_no_assignment_for_new_doc(self):
        """
        [TC-V-002]
        Mục tiêu: Với Task mới (chưa insert) hoặc không có assigned_to, validate() không gọi assignment nào.
        Input: Task mới với assigned_to = None.
        Expected Output: Không có lời gọi đến assign_to hay unassign.
        Note: Dùng patch.
        """
        task = frappe.new_doc("CRM Task")
        task.title = "Test Validate New"
        task.assigned_to = None
        with patch.object(task, "assign_to") as mock_assign, \
             patch.object(task, "unassign_from_previous_user") as mock_unassign:
            task.validate()
            mock_assign.assert_not_called()
            mock_unassign.assert_not_called()

    def test_validate_no_change_in_assignment(self):
        """
        [TC-V-003]
        Mục tiêu: Nếu không có thay đổi value của assigned_to khi cập nhật Task, validate() không gọi lại assign_to/unassign_from_previous_user.
        Input: Task có assigned_to = "Administrator", cập nhật field khác.
        Expected Output: Không có lời gọi đến assign_to hay unassign_from_previous_user.
        """
        task = self.create_crm_task(assigned_to="Administrator")
        with patch.object(task, "get_doc_before_save", return_value=type("Dummy", (object,), {"assigned_to": "Administrator"})):
            with patch.object(task, "assign_to") as mock_assign, \
                 patch.object(task, "unassign_from_previous_user") as mock_unassign:
                task.title = "Updated Title"
                task.validate()
                mock_assign.assert_not_called()
                mock_unassign.assert_not_called()

    def test_validate_missing_required_field(self):
        """
        [TC-V-004]
        Mục tiêu: Validate thất bại nếu thiếu trường bắt buộc (ví dụ: title).
        Input: Task mới mà không gán title.
        Expected Output: Khi insert, raise exception validate.
        """
        task = frappe.new_doc("CRM Task")
        # Không gán title (title được reqd theo crm_task.json)
        task.assigned_to = "Administrator"
        with self.assertRaises(Exception):
            task.insert(ignore_permissions=True)

    # ============================
    # 3. Test hàm assign_to()
    # ============================
    def test_assign_to_calls_module_assign(self):
        """
        [TC-AT-001]
        Mục tiêu: Nếu assigned_to có giá trị hợp lệ, assign_to() sẽ gọi hàm assign của module bên ngoài.
        Input: Task có assigned_to = "Administrator".
        Expected Output: Task được lưu vào hệ thống với assigned_to = "Administrator"
        Note: Dùng patch.
        """
        task = self.create_crm_task(assigned_to="Administrator")
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            task.assign_to()
            mock_assign.assert_called_once()
            args, kwargs = mock_assign.call_args
            self.assertEqual(args[0].get("assign_to"), ["Administrator"])

    def test_assign_to_no_action_for_empty(self):
        """
        [TC-AT-002]
        Mục tiêu: Nếu assigned_to rỗng, assign_to() không gọi hàm assign của module.
        Input: Task có assigned_to = "".
        Expected Output: Không có lời gọi đến assign.
        Note: Dùng patch.
        """
        task = self.create_crm_task(assigned_to="")
        with patch("crm.fcrm.doctype.crm_task.crm_task.assign") as mock_assign:
            task.assign_to()
            mock_assign.assert_not_called()

    def test_assign_to_invalid_assigned_to(self):
        """
        [TC-AT-003]
        Mục tiêu: Nếu assigned_to là user không tồn tại, khi insert Task sẽ raise LinkValidationError.
        """
        invalid_user = "nonexistent@example.com"
        # Đảm bảo user này không có trong DB
        if frappe.db.exists("User", invalid_user):
            frappe.delete_doc("User", invalid_user, force=True)
            frappe.db.commit()
        # Tạo Task với assigned_to không hợp lệ -> lỗi LinkValidationError
        with self.assertRaises(frappe.LinkValidationError):
            self.create_crm_task(assigned_to=invalid_user)

    # ============================
    # 4. Test hàm unassign_from_previous_user()
    # ============================
    def test_unassign_from_previous_user_calls_module_unassign(self):
        """
        [TC-UAPU-001]
        Mục tiêu: Khi gọi unassign_from_previous_user với user hợp lệ, hàm sẽ gọi module unassign.
        Input: user = "Administrator"
        Expected Output: Hàm unassign được gọi với doctype, name của task và user.
        Note: Dùng patch.
        """
        task = self.create_crm_task()
        with patch("crm.fcrm.doctype.crm_task.crm_task.unassign") as mock_unassign:
            task.unassign_from_previous_user("Administrator")
            mock_unassign.assert_called_once_with(task.doctype, task.name, "Administrator")

    def test_unassign_from_previous_user_with_empty(self):
        """
        [TC-UAPU-002]
        Mục tiêu: Nếu truyền user rỗng, unassign_from_previous_user() không gọi hàm unassign.
        Input: user = "".
        Expected Output: Không có lời gọi đến unassign.
        Note: Dùng patch.
        """
        task = self.create_crm_task()
        with patch("crm.fcrm.doctype.crm_task.crm_task.unassign") as mock_unassign:
            task.unassign_from_previous_user("")
            mock_unassign.assert_not_called()

    def test_unassign_from_previous_user_nonexistent(self):
        """
        [TC-UAPU-003]
        Mục tiêu: Khi truyền user không tồn tại, hệ thống cần raise exception (hoặc xử lý lỗi theo nghiệp vụ).
        Input: user = "nonexistent@example.com"
        Expected Output: Raise exception.
        Note: Dùng patch với side_effect.
        """
        task = self.create_crm_task()
        with patch("crm.fcrm.doctype.crm_task.crm_task.unassign", side_effect=Exception("User not found")):
            with self.assertRaises(Exception):
                task.unassign_from_previous_user("nonexistent@example.com")

    # ============================
    # 5. Test hàm default_list_data()
    # ============================
    def test_default_list_data(self):
        """
        [TC-DLD-001]
        Mục tiêu: Kiểm tra cấu trúc dictionary trả về từ default_list_data.
        Input: Không cần input.
        Expected Output: Dictionary có key "columns" (dạng list) và "rows".
        Note: Dùng assertIn và assertIsInstance.
        """
        data = CRMTask.default_list_data()
        self.assertIsInstance(data, dict)
        self.assertIn("columns", data)
        self.assertIsInstance(data["columns"], list)
        self.assertIn("rows", data)

    # ============================
    # 6. Test hàm default_kanban_settings()
    # ============================
    def test_default_kanban_settings(self):
        """
        [TC-DKS-001]
        Mục tiêu: Kiểm tra dictionary trả về từ default_kanban_settings chứa các key cần thiết.
        Input: Không cần input.
        Expected Output: Dictionary chứa các key "column_field", "title_field", "kanban_fields".
        Note: Dùng assertIn.
        """
        settings = CRMTask.default_kanban_settings()
        self.assertIsInstance(settings, dict)
        self.assertIn("column_field", settings)
        self.assertIn("title_field", settings)
        self.assertIn("kanban_fields", settings)

           # ===================================================
    # 7. Test CRUD Operations: Insert, Get, Update, Delete
    # ===================================================
    def test_insert_valid_task(self):
        """TC-INS-01: Tạo mới Task hợp lệ."""
        before = frappe.db.count("CRM Task")
        task = self.create_crm_task(title="CRUD Test Insert", status="Todo")
        frappe.db.commit()
        after = frappe.db.count("CRM Task")

        self.assertTrue(task.name)
        self.assertEqual(task.title, "CRUD Test Insert")
        self.assertEqual(after, before + 1)

    def test_insert_missing_title(self):
        """TC-INS-02: Insert thất bại khi thiếu trường title."""
        before = frappe.db.count("CRM Task")
        with self.assertRaises(frappe.MandatoryError):
            frappe.get_doc({
                "doctype": "CRM Task",
                # title bị bỏ qua
                "priority": "High",
                "assigned_to": self.test_user,
                "status": "Todo"
            }).insert(ignore_permissions=True)
        frappe.db.rollback()
        after = frappe.db.count("CRM Task")
        self.assertEqual(after, before)

    def test_insert_invalid_due_date(self):
        """TC-INS-03: Insert thất bại khi due_date sai định dạng."""
        before = frappe.db.count("CRM Task")
        with self.assertRaises(Exception):
            self.create_crm_task(extra_fields={"due_date": "not-a-date"})
        frappe.db.rollback()
        after = frappe.db.count("CRM Task")
        self.assertEqual(after, before)

    def test_insert_past_due_date(self):
        """TC-INS-04: Insert thất bại khi due_date là ngày trong quá khứ."""
        from datetime import date, timedelta

        # Lấy ngày hôm qua
        past_date = (date.today() - timedelta(days=1)).isoformat()
        before = frappe.db.count("CRM Task")

        # Thử tạo Task với due_date ở quá khứ, mong đợi ValidationError
        with self.assertRaises(frappe.ValidationError):
            self.create_crm_task(
                title="CRUD Test Past Due",
                status="Todo",
                extra_fields={"due_date": past_date}
            )
        # Rollback để đảm bảo DB không thay đổi
        frappe.db.rollback()
        after = frappe.db.count("CRM Task")
        self.assertEqual(after, before)


    def test_get_existing_task(self):
        """TC-GET-01: Lấy Task tồn tại thành công."""
        before = frappe.db.count("CRM Task")
        task = self.create_crm_task(title="CRUD Test Get", status="Todo")
        fetched = frappe.get_doc("CRM Task", task.name)
        frappe.db.commit()
        after = frappe.db.count("CRM Task")

        self.assertEqual(fetched.title, "CRUD Test Get")
        self.assertEqual(after, before + 1)

    def test_get_nonexistent_task(self):
        """TC-GET-02: Lấy Task không tồn tại gây lỗi."""
        before = frappe.db.count("CRM Task")
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.get_doc("CRM Task", "does-not-exist")
        frappe.db.rollback()
        after = frappe.db.count("CRM Task")
        self.assertEqual(after, before)

    def test_update_status(self):
        """TC-UPD-01: Cập nhật status từ 'Todo' → 'Done'."""
        task = self.create_crm_task(status="Todo")
        task.reload()
        before_status = frappe.get_value("CRM Task", task.name, "status")

        task.flags.ignore_version_mismatch = True
        task.status = "Done"
        task.save(ignore_permissions=True)
        frappe.db.commit()
        after_status = frappe.get_value("CRM Task", task.name, "status")

        self.assertNotEqual(before_status, after_status)
        self.assertEqual(after_status, "Done")

    def test_update_no_changes(self):
        """TC-UPD-02: Gọi save() khi không thay đổi field không gây assign/unassign."""
        task = self.create_crm_task()
        task.reload()
        before_modified = frappe.get_value("CRM Task", task.name, "modified")

        task.flags.ignore_version_mismatch = True
        with patch.object(task, "assign_to") as mock_assign, \
             patch.object(task, "unassign_from_previous_user") as mock_unassign:
            task.save(ignore_permissions=True)
            frappe.db.commit()
            mock_assign.assert_not_called()
            mock_unassign.assert_not_called()

        after_modified = frappe.get_value("CRM Task", task.name, "modified")
        self.assertEqual(after_modified, before_modified)

    def test_update_invalid_due_date(self):
        """TC-UPD-03: Cập nhật thất bại khi due_date sai định dạng."""
        task = self.create_crm_task()
        task.reload()
        before_due = frappe.get_value("CRM Task", task.name, "due_date")

        task.flags.ignore_version_mismatch = True
        task.due_date = "bad-format"
        with self.assertRaises(Exception):
            task.save(ignore_permissions=True)
        frappe.db.rollback()

        after_due = frappe.get_value("CRM Task", task.name, "due_date")
        self.assertEqual(after_due, before_due)

    def test_update_multiple_fields(self):
        """TC-UPD-04: Cập nhật đồng thời status và priority."""
        task = self.create_crm_task(status="Todo", priority="High")
        task.reload()

        task.flags.ignore_version_mismatch = True
        task.status = "In Progress"
        task.priority = "Low"
        task.save(ignore_permissions=True)
        frappe.db.commit()

        updated = frappe.get_doc("CRM Task", task.name)
        self.assertEqual(updated.status, "In Progress")
        self.assertEqual(updated.priority, "Low")

    def test_delete_task_success(self):
        """TC-DEL-01: Xóa Task không có liên kết thành công."""
        task = self.create_crm_task()
        before = frappe.db.count("CRM Task")

        # dọn dẹp Notification nếu có
        for n in frappe.get_all("CRM Notification", filters={"notification_type_doc": task.name}):
            frappe.delete_doc("CRM Notification", n.name, force=True)
        task.delete(ignore_permissions=True)
        frappe.db.commit()
        after = frappe.db.count("CRM Task")

        self.assertEqual(after, before - 1)
        self.assertFalse(frappe.db.exists("CRM Task", task.name))

    def test_delete_nonexistent_task(self):
        """TC-DEL-02: Xóa Task không tồn tại gây lỗi."""
        before = frappe.db.count("CRM Task")
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.delete_doc("CRM Task", "no-such-task", force=True)
        frappe.db.rollback()
        after = frappe.db.count("CRM Task")
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
