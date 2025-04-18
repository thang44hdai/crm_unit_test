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
        
    def tearDown(self):
        # Rollback tất cả các thay đổi trong cơ sở dữ liệu
        frappe.db.rollback()

    #Note-01: Tạo một FCRM Note mới với đầy đủ nội dung
    def test_create_fcrm_note(self):
        note = frappe.get_doc({
            "doctype": "FCRM Note", #Cố định
            "title": "test 9/4",
            "content": "<p>hello</p>",
            "reference_doctype": "CRM Lead", #Cố định
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
        # Lấy lại note vừa tạo
        saved_note = frappe.get_doc("FCRM Note", note.name)

        # Kiểm tra các trường
        self.assertEqual(saved_note.title, "test 9/4")
        self.assertEqual(saved_note.content, "<p>hello</p>")
        self.assertEqual(saved_note.reference_doctype, "CRM Lead")
        self.assertEqual(saved_note.reference_docname, "CRM-LEAD-2025-00001")
        self.assertEqual(saved_note.owner, "Administrator")
        
    #Note-02: Tạo FCRM Note không có tiêu đề
    def test_create_fcrm_note_without_title(self):
        #Kiểm tra xem có thể lưu vào database không
        with self.assertRaises(frappe.MandatoryError):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "content": "<p>Content without Title</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
            
    #Note-03: Tạo FCRM Note mà không thuộc Leads nào
    def test_create_fcrm_note_with_invalid_reference(self):
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "test 9/4",
            "content": "<p>hello</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": ""
        }).insert(ignore_permissions=True)
        # Lấy lại note vừa tạo
        saved_note = frappe.get_doc("FCRM Note", note.name)

        # Kiểm tra các trường
        self.assertEqual(saved_note.title, "test 9/4")
        self.assertEqual(saved_note.content, "<p>hello</p>")
        self.assertEqual(saved_note.reference_doctype, "CRM Lead")
        self.assertEqual(saved_note.reference_docname, "")
        self.assertEqual(saved_note.owner, "Administrator")
    
    #Note-04: Tạo FCRM Note mà không có nội dung  
    def test_create_fcrm_note_without_content(self):
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Note without Content",
            "content": "",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Lấy lại ghi chú vừa tạo
        saved_note = frappe.get_doc("FCRM Note", note.name)
    
        # Kiểm tra các trường
        self.assertEqual(saved_note.title, "Note without Content")
        self.assertEqual(saved_note.content, "")
  
    #Note-05: Kiểm tra SQL Injection khi tạo FCRM Note
    def test_create_fcrm_note_with_sql_injection(self):
        # Chuỗi SQL Injection
        sql_injection_string = "'; DROP TABLE `tabFCRM Note`; --"

        # Tạo ghi chú với chuỗi SQL Injection trong title
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": sql_injection_string,
            "content": "<p>Content with SQL Injection</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)

        # Lấy lại ghi chú vừa tạo
        saved_note = frappe.get_doc("FCRM Note", note.name)

        # Kiểm tra rằng ghi chú được tạo thành công và không bị lỗi SQL Injection
        self.assertEqual(saved_note.title, sql_injection_string)
        self.assertEqual(saved_note.content, "<p>Content with SQL Injection</p>")

        # Kiểm tra rằng bảng `tabFCRM Note` vẫn tồn tại
        self.assertTrue(frappe.db.exists("DocType", "FCRM Note"))
        
    #Note-06: Kiểm tra chèn HTML vào title và content khi tạo FCRM Note
    def test_create_fcrm_note_with_html_in_title_and_content(self):
        # Chuỗi HTML để chèn vào title và content
        html_title = "<script>alert(1)</script>"
        html_content = "<p><strong>HTML Content</strong></p>"
    
        # Tạo ghi chú với HTML trong title và content
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": html_title,
            "content": html_content,
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Lấy lại ghi chú vừa tạo
        saved_note = frappe.get_doc("FCRM Note", note.name)
    
        # Kiểm tra rằng HTML được lưu trữ đúng
        self.assertEqual(saved_note.title, html_title)
        self.assertEqual(saved_note.content, html_content)
    
        # Kiểm tra rằng bảng `tabFCRM Note` vẫn tồn tại
        self.assertTrue(frappe.db.exists("DocType", "FCRM Note"))

    # Note-07: Tạo FCRM Note với title vượt quá giới hạn ký tự
    def test_create_fcrm_note_with_exceeding_title_length(self):
        # Chuỗi title vượt quá giới hạn ký tự (giả sử giới hạn là 255 ký tự)
        long_title = "A" * 256  # 256 ký tự

        # Kiểm tra rằng lỗi CharacterLengthExceededError được ném ra
        with self.assertRaises(frappe.CharacterLengthExceededError):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": long_title,
                "content": "<p>Content with long title</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
            
    #Note-08: Cập nhật một FCRM Note với đầy đủ nội dung
    def test_update_fcrm_note(self):
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Cập nhật ghi chú
        note.title = "Updated Title"
        note.content = "<p>Updated Content</p>"
        note.save(ignore_permissions=True)
    
        # Lấy lại ghi chú đã cập nhật
        updated_note = frappe.get_doc("FCRM Note", note.name)
    
        # Kiểm tra các trường đã được cập nhật
        self.assertEqual(updated_note.title, "Updated Title")
        self.assertEqual(updated_note.content, "<p>Updated Content</p>")
       
    #Note-09: Cập nhật một FCRM Note nhưng xóa hết title và content
    def test_update_fcrm_note_with_empty_title_and_content(self):
        # Tạo một FCRM Note mới
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Cập nhật ghi chú, xóa hết title và content
        note.title = ""
        note.content = ""
        with self.assertRaises(frappe.MandatoryError):
            note.save(ignore_permissions=True)
    
        # Lấy lại ghi chú từ cơ sở dữ liệu để kiểm tra dữ liệu không bị thay đổi
        saved_note = frappe.get_doc("FCRM Note", note.name)
        self.assertEqual(saved_note.title, "Initial Title")
        self.assertEqual(saved_note.content, "<p>Initial Content</p>")
         
    # Note-10: Cập nhật FCRM Note với title vượt quá giới hạn ký tự
    def test_update_fcrm_note_with_exceeding_title_length(self):
        # Tạo một FCRM Note mới
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Cập nhật title vượt quá giới hạn ký tự
        long_title = "A" * 256  # 256 ký tự
        note.title = long_title
    
        # Kiểm tra rằng lỗi CharacterLengthExceededError được ném ra
        with self.assertRaises(frappe.CharacterLengthExceededError):
            note.save(ignore_permissions=True)
    
    # Note-11: Cập nhật FCRM Note với SQL Injection
    def test_update_fcrm_note_with_sql_injection(self):
        # Tạo một FCRM Note mới
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Cập nhật title và content với SQL Injection
        sql_injection_string = "'; DROP TABLE `tabFCRM Note`; --"
        note.title = sql_injection_string
        note.content = sql_injection_string
        note.save(ignore_permissions=True)
    
        # Lấy lại ghi chú đã cập nhật
        updated_note = frappe.get_doc("FCRM Note", note.name)
    
        # Kiểm tra rằng SQL Injection không gây ảnh hưởng
        self.assertEqual(updated_note.title, sql_injection_string)
        self.assertEqual(updated_note.content, sql_injection_string)
        self.assertTrue(frappe.db.exists("DocType", "FCRM Note"))
    
    # Note-12: Cập nhật FCRM Note với HTML trong title và content
    def test_update_fcrm_note_with_html(self):
        # Tạo một FCRM Note mới
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Initial Title",
            "content": "<p>Initial Content</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Cập nhật title và content với HTML
        html_title = "<script>alert(1)</script>"
        html_content = "<p><strong>Updated HTML Content</strong></p>"
        note.title = html_title
        note.content = html_content
        note.save(ignore_permissions=True)
    
        # Lấy lại ghi chú đã cập nhật
        updated_note = frappe.get_doc("FCRM Note", note.name)
    
        # Kiểm tra rằng HTML được lưu trữ đúng
        self.assertEqual(updated_note.title, html_title)
        self.assertEqual(updated_note.content, html_content)
    
    #Note-13: Lấy danh sách FCRM Note
    def test_get_fcrm_note_list(self):
        for i in range(3):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
    
        # Lấy danh sách ghi chú
        notes = frappe.get_list("FCRM Note", filters={"reference_doctype": "CRM Lead"}, fields=["name", "title"])
    
        # Kiểm tra danh sách ghi chú có size >= 3 không
        self.assertGreaterEqual(len(notes), 3)
    
    #Note-14: Lấy danh sách FCRM Note với title chứa ký tự cho trước
    def test_get_fcrm_note_list_with_title_filter(self):
        for i in range(3):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Filtered Title {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
    
        # Lấy danh sách ghi chú với title chứa "Filtered"
        notes = frappe.get_list("FCRM Note", filters={"title": ["like", "%Filtered%"]}, fields=["name", "title"])
    
        # Kiểm tra danh sách ghi chú có size >= 3 không
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertIn("Filtered", note.title)
    
    #Note-15: Lấy danh sách FCRM Note với content chứa ký tự cho trước
    def test_get_fcrm_note_list_with_content_filter(self):
        for i in range(3):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Filtered Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
    
        # Lấy danh sách ghi chú với content chứa "Filtered"
        notes = frappe.get_list("FCRM Note", filters={"content": ["like", "%Filtered%"]}, fields=["name", "content"])
    
        # Kiểm tra danh sách ghi chú có size >= 3 không
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertIn("Filtered", note.content)
    
    #Note-16: Lấy danh sách FCRM Note với name chứa ký tự cho trước
    def test_get_fcrm_note_list_with_name_filter(self):
        # Debug: Kiểm tra các bản ghi hiện có trong database
        all_notes = frappe.get_all("FCRM Note", fields=["name"])

        # Lấy danh sách ghi chú với name chứa "vo30o9"
        notes = frappe.get_list(
            "FCRM Note",
            filters={"name": ["like", "%vo30o9%"]},
            fields=["*"]  # Lấy tất cả các trường
        )

        # Kiểm tra từng bản ghi
        for note in notes:
            # Kiểm tra name chứa "vo30o9"
            self.assertIn("vo30o9", note.name)
    
    #Note-17: Lấy danh sách FCRM Note với reference_doctype chứa ký tự cho trước
    def test_get_fcrm_note_list_with_reference_doctype_filter(self):
        for i in range(3):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": "CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
    
        # Lấy danh sách ghi chú với reference_doctype là "CRM Lead"
        notes = frappe.get_list("FCRM Note", filters={"reference_doctype": "CRM Lead"}, fields=["name", "reference_doctype"])
    
        # Kiểm tra danh sách ghi chú
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertEqual(note.reference_doctype, "CRM Lead")
    
    #Note-18: Lấy danh sách FCRM Note với reference_docname chứa ký tự cho trước
    def test_get_fcrm_note_list_with_reference_docname_filter(self):
        for i in range(3):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": f"CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
            
        frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"<p>Content {i+1}</p>",
                "reference_doctype": "CRM Lead",
                "reference_docname": f"CRM-LEAD-2025-00002"
            }).insert(ignore_permissions=True)
        
        # Lấy danh sách ghi chú với reference_docname chứa "CRM-LEAD"
        notes = frappe.get_list("FCRM Note", filters={"reference_docname": ["like", "%CRM-LEAD-2025-00001%"]}, fields=["name", "reference_docname"])
    
        # Kiểm tra danh sách ghi chú
        self.assertGreaterEqual(len(notes), 3)
        for note in notes:
            self.assertIn("CRM-LEAD-2025-00001", note.reference_docname)

    # Note-19: Sắp xếp danh sách FCRM Note theo title
    def test_sort_fcrm_note_by_title(self):
        # Lấy danh sách ghi chú sắp xếp theo title
        notes = frappe.get_list("FCRM Note", fields=["title"], order_by="title asc")

        # Kiểm tra thứ tự sắp xếp
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["title"], notes[i - 1]["title"])
    
    # Note-20: Sắp xếp danh sách FCRM Note theo content
    def test_sort_fcrm_note_by_content(self):
        # Lấy danh sách ghi chú sắp xếp theo content
        notes = frappe.get_list("FCRM Note", fields=["content"], order_by="content asc")

        # Kiểm tra thứ tự sắp xếp
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["content"], notes[i - 1]["content"])
            
    # Note-21: Sắp xếp danh sách FCRM Note theo name
    def test_sort_fcrm_note_by_name(self):
        for i in range(3):
            frappe.get_doc({
                "doctype": "FCRM Note",
                "title": f"Note {i+1}",
                "content": f"Content {i+1}",
                "reference_doctype": "CRM Lead",
                "reference_docname": f"CRM-LEAD-2025-00001"
            }).insert(ignore_permissions=True)
    
        # Lấy danh sách ghi chú sắp xếp theo name
        notes = frappe.get_list("FCRM Note", fields=["name"], order_by="name asc")
    
        # Kiểm tra thứ tự sắp xếp
        self.assertTrue(notes[0].name < notes[1].name < notes[2].name)
        
    # Note-22: Sắp xếp danh sách FCRM Note theo reference_doctype
    def test_sort_fcrm_note_by_reference_doctype(self):
        # Lấy danh sách ghi chú sắp xếp theo reference_doctype
        notes = frappe.get_list("FCRM Note", fields=["reference_doctype"], order_by="reference_doctype asc")

        # Kiểm tra thứ tự sắp xếp
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["reference_doctype"], notes[i - 1]["reference_doctype"])
    
    # Note-23: Sắp xếp danh sách FCRM Note theo reference_docname
    def test_sort_fcrm_note_by_reference_docname(self):
        # Lấy danh sách ghi chú sắp xếp theo reference_docname
        notes = frappe.get_list("FCRM Note", fields=["reference_docname"], order_by="reference_docname asc")

        # Kiểm tra thứ tự sắp xếp
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["reference_docname"], notes[i - 1]["reference_docname"])

    # Note24: Sắp xếp danh sách FCRM Note theo ngày tạo
    def test_sort_fcrm_note_by_creation(self):
        # Lấy danh sách ghi chú sắp xếp theo ngày tạo
        notes = frappe.get_list("FCRM Note", fields=["creation"], order_by="creation asc")

        # Kiểm tra thứ tự sắp xếp
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["creation"], notes[i - 1]["creation"])
    
    # Note-25: Sắp xếp danh sách FCRM Note theo ngày cập nhật
    def test_sort_fcrm_note_by_modified(self):
        # Lấy danh sách ghi chú sắp xếp theo ngày cập nhật
        notes = frappe.get_list("FCRM Note", fields=["modified"], order_by="modified asc")

        # Kiểm tra thứ tự sắp xếp
        for i in range(1, len(notes)):
            self.assertGreaterEqual(notes[i]["modified"], notes[i - 1]["modified"])
            
    # Note-26: Xóa FCRM Note
    # Kiểm tra việc xóa một FCRM Note
    def test_delete_fcrm_note(self):
        # Tạo một FCRM Note mới
        note = frappe.get_doc({
            "doctype": "FCRM Note",
            "title": "Note to be Deleted",
            "content": "<p>Content to be Deleted</p>",
            "reference_doctype": "CRM Lead",
            "reference_docname": "CRM-LEAD-2025-00001"
        }).insert(ignore_permissions=True)
    
        # Lấy tên của ghi chú vừa tạo
        note_name = note.name
    
        # Xóa ghi chú
        frappe.delete_doc("FCRM Note", note_name, ignore_permissions=True)
    
        # Kiểm tra rằng ghi chú đã bị xóa
        with self.assertRaises(frappe.DoesNotExistError):
            frappe.get_doc("FCRM Note", note_name)
    
        # Kiểm tra rằng ghi chú không còn tồn tại trong cơ sở dữ liệu
        self.assertFalse(frappe.db.exists("FCRM Note", note_name))