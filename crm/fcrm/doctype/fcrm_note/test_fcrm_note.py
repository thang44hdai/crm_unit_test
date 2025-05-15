from frappe.tests.utils import FrappeTestCase
import frappe
from crm.fcrm.doctype.fcrm_note.fcrm_note import FCRMNote

class TestFCRMNoteFunctions(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.begin()

    def tearDown(self):
        frappe.db.rollback()

    # Note-01: Tạo một FCRM Note mới với đầy đủ nội dung
    def test_create_fcrm_note(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "test 9/4",
            "content": "<p>hello</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        saved_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(saved_note.title, "test 9/4")
        self.assertEqual(saved_note.content, "<p>hello</p>")
        self.assertEqual(saved_note.reference_doctype, "CRM Lead")
        self.assertEqual(saved_note.reference_docname, "CRM-LEAD-2025-00001")

    # Note-02: Tạo FCRM Note không có tiêu đề
    def test_create_fcrm_note_without_title(self):
        ## Hàm assertRaises check ngoại lệ có phải là MandatoryError: lỗi thiếu trường bắt buộc
        with self.assertRaises(frappe.MandatoryError):
            FCRMNote({
                "doctype": "FCRM Note",
                "content": "<p>Content without Title</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert()

    # Note-04: Tạo FCRM Note mà không có nội dung
    def test_create_fcrm_note_without_content(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Note without Content",
            "content": "",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        saved_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(saved_note.content, "")

    # Note-05: Kiểm tra SQL Injection khi tạo FCRM Note
    def test_create_fcrm_note_with_sql_injection(self):
        sql_injection_string = "'; DROP TABLE `tabFCRM Note`; --"
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": sql_injection_string,
            "content": "<p>Content with SQL Injection</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        saved_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(saved_note.title, sql_injection_string)
        self.assertTrue(frappe.db.exists("DocType", "FCRM Note"))

    # Note-06: Kiểm tra chèn HTML vào title và content khi tạo FCRM Note
    def test_create_fcrm_note_with_html_in_title_and_content(self):
        html_title = "<script>alert(1)</script>"
        html_content = "<p><strong>HTML Content</strong></p>"
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": html_title,
            "content": html_content,
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        saved_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(saved_note.title, html_title)
        self.assertEqual(saved_note.content, html_content)

    # Note-07: Tạo FCRM Note với title vượt quá giới hạn ký tự
    def test_create_fcrm_note_with_exceeding_title_length(self):
        long_title = "A" * 256
        with self.assertRaises(frappe.CharacterLengthExceededError):
            FCRMNote({
                "doctype": "FCRM Note",
                "title": long_title,
                "content": "<p>Content with long title</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert()

    # Note-08: Cập nhật một FCRM Note với đầy đủ nội dung
    def test_update_fcrm_note(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        note.title = "Updated Title"
        note.content = "<p>Updated Content</p>"
        note.save()
        updated_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(updated_note.title, "Updated Title")
        self.assertEqual(updated_note.content, "<p>Updated Content</p>")

    # Note-09: Cập nhật một FCRM Note nhưng xóa hết title và content
    def test_update_fcrm_note_with_empty_title_and_content(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        note.title = ""
        note.content = ""
        with self.assertRaises(frappe.MandatoryError):
            note.save()

    # Note-10: Cập nhật FCRM Note với title vượt quá giới hạn ký tự
    def test_update_fcrm_note_with_exceeding_title_length(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        note.title = "A" * 256
        with self.assertRaises(frappe.CharacterLengthExceededError):
            note.save()

    # Note-11: Cập nhật FCRM Note với SQL Injection
    def test_update_fcrm_note_with_sql_injection(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        sql_injection_string = "'; DROP TABLE `tabFCRM Note`; --"
        note.title = sql_injection_string
        note.content = sql_injection_string
        note.save()
        updated_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(updated_note.title, sql_injection_string)
        self.assertEqual(updated_note.content, sql_injection_string)
        self.assertTrue(frappe.db.exists("DocType", "FCRM Note"))

    # Note-12: Cập nhật FCRM Note với HTML trong title và content
    def test_update_fcrm_note_with_html(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        html_title = "<script>alert(1)</script>"
        html_content = "<p><strong>Updated HTML Content</strong></p>"
        note.title = html_title
        note.content = html_content
        note.save()
        updated_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(updated_note.title, html_title)
        self.assertEqual(updated_note.content, html_content)

    # Note-13: Lấy danh sách FCRM Note
    def test_get_fcrm_note_list(self):
        for i in range(3):
            FCRMNote({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert()
        notes = frappe.get_list("FCRM Note", filters={"reference_doctype": "CRM Lead"}, fields=["*"])
        self.assertGreaterEqual(len(notes), 3)

    # Note-14: Lấy danh sách FCRM Note với title chứa ký tự cho trước
    def test_get_fcrm_note_list_with_title_filter(self):
        for i in range(3):
            FCRMNote({
                "doctype": "FCRM Note",
                "title": f"Filtered Title {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert()
        notes = frappe.get_list("FCRM Note", filters={"title": ["like", "%Filtered%"]}, fields=["*"])
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertIn("Filtered", note.title)

    # Note-15: Lấy danh sách FCRM Note với content chứa ký tự cho trước
    def test_get_fcrm_note_list_with_content_filter(self):
        for i in range(3):
            FCRMNote({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Filtered Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert()
        notes = frappe.get_list("FCRM Note", filters={"content": ["like", "%Filtered%"]}, fields=["*"])
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertIn("Filtered", note.content)

    # Note-16: Lấy danh sách FCRM Note với name chứa ký tự cho trước
    def test_get_fcrm_note_list_with_name_filter(self):
        notes = frappe.get_list("FCRM Note", filters={"name": ["like", "%vo30o9%"]}, fields=["*"])
        for note in notes:
            self.assertIn("vo30o9", note.name)

    # Note-17: Lấy danh sách FCRM Note với reference_doctype chứa ký tự cho trước
    def test_get_fcrm_note_list_with_reference_doctype_filter(self):
        for i in range(3):
            FCRMNote({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert()
        notes = frappe.get_list("FCRM Note", filters={"reference_doctype": "CRM Lead"}, fields=["*"])
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertEqual(note.reference_doctype, "CRM Lead")

    # Note-19: Sắp xếp danh sách FCRM Note theo title
    def test_sort_fcrm_note_by_title(self):
        notes = frappe.get_list("FCRM Note", order_by="title asc", fields=["*"])
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["title"], notes[i - 1]["title"])

    # Note-20: Sắp xếp danh sách FCRM Note theo content
    def test_sort_fcrm_note_by_content(self):
        notes = frappe.get_list("FCRM Note", order_by="content asc", fields=["*"])
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["content"], notes[i - 1]["content"])

    # Note-21: Sắp xếp danh sách FCRM Note theo name
    def test_sort_fcrm_note_by_name(self):
        for i in range(3):
            FCRMNote({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"Content {i+1}",
                "reference_doctype": "CRM Lead",
                "reference_docname": f"CRM-LEAD-2025-00001"
            }).insert()
        notes = frappe.get_list("FCRM Note", order_by="name asc", fields=["*"])
        self.assertTrue(notes[0].name < notes[1].name < notes[2].name)

    # Note-22: Sắp xếp danh sách FCRM Note theo reference_doctype
    def test_sort_fcrm_note_by_reference_doctype(self):
        notes = frappe.get_list("FCRM Note", order_by="reference_doctype asc", fields=["*"])
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["reference_doctype"], notes[i - 1]["reference_doctype"])

    # Note-23: Sắp xếp danh sách FCRM Note theo reference_docname
    def test_sort_fcrm_note_by_reference_docname(self):
        notes = frappe.get_list("FCRM Note", order_by="reference_docname asc", fields=["*"])
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["reference_docname"], notes[i - 1]["reference_docname"])

    # Note-24: Sắp xếp danh sách FCRM Note theo ngày tạo
    def test_sort_fcrm_note_by_creation(self):
        notes = frappe.get_list("FCRM Note", order_by="creation asc", fields=["*"])
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["creation"], notes[i - 1]["creation"])

    # Note-25: Sắp xếp danh sách FCRM Note theo ngày cập nhật
    def test_sort_fcrm_note_by_modified(self):
        notes = frappe.get_list("FCRM Note", order_by="modified asc", fields=["*"])
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["modified"], notes[i - 1]["modified"])

    # Note-26: Xóa FCRM Note
    def test_delete_fcrm_note(self):
        note = FCRMNote({
            "doctype": "FCRM Note",
            "title": "Note to be Deleted",
            "content": "<p>Content to be Deleted</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert()
        note_name = note.name
        note.delete()
        # Kiểm tra note đã bị xóa khỏi database
        self.assertFalse(frappe.db.exists("FCRM Note", note_name))