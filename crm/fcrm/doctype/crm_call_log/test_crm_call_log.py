import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock

from crm.fcrm.doctype.crm_call_log.crm_call_log import (
    CRMCallLog,
    parse_call_log,
    get_call_log,
    create_lead_from_call_log
)

class TestCRMCallLog(FrappeTestCase):
    # Mỗi test sẽ được rollback tự động nhờ FrappeTestCase

    def setUp(self):
        super().setUp()
        # Giả lập hàm seconds_to_duration luôn trả về chuỗi cố định
        patcher = patch(
            'crm.fcrm.doctype.crm_call_log.crm_call_log.seconds_to_duration',
            return_value='00:01:23'
        )
        self.mock_seconds = patcher.start()
        self.addCleanup(patcher.stop)

    def test_default_list_data_structure_TC_CALLLOG_001(self):
        """
        TC_CALLLOG_001: Kiểm tra default_list_data trả về dict chứa 'columns' và 'rows',
        columns phải là list các dict có 'label' và 'key', rows là list chuỗi.
        """
        result = CRMCallLog.default_list_data()
        self.assertIn('columns', result)
        self.assertIn('rows', result)

        columns = result['columns']
        self.assertIsInstance(columns, list)
        for col in columns:
            self.assertIsInstance(col, dict)
            self.assertIn('label', col)
            self.assertIn('key', col)

        rows = result['rows']
        self.assertIsInstance(rows, list)
        for r in rows:
            self.assertIsInstance(r, str)

    def test_parse_list_data_empty_TC_CALLLOG_002(self):
        """
        TC_CALLLOG_002: parse_list_data(None) và parse_list_data([])
        phải trả về list rỗng.
        """
        self.assertEqual(CRMCallLog.parse_list_data([]), [])
        self.assertEqual(CRMCallLog.parse_list_data(None), [])

    def test_has_and_link_with_reference_doc_TC_CALLLOG_003(self):
        """
        TC_CALLLOG_003: has_link False khi chưa có, link_with_reference_doc
        thêm mới link, không duplicate khi gọi lại.
        """
        # Tạo document mới đúng kiểu Frappe
        doc = frappe.new_doc("CRM Call Log")
        # Ban đầu không có link
        self.assertFalse(doc.has_link('DummyDoc', 'D1'))
        # Thêm link
        doc.link_with_reference_doc('DummyDoc', 'D1')
        self.assertTrue(doc.has_link('DummyDoc', 'D1'))
        # Gọi lại không thêm bản ghi mới
        count_before = len(doc.links)
        doc.link_with_reference_doc('DummyDoc', 'D1')
        self.assertEqual(len(doc.links), count_before)

    @patch('crm.fcrm.doctype.crm_call_log.crm_call_log.get_contact_by_phone_number')
    @patch('frappe.db.get_values')
    def test_parse_call_log_incoming_TC_CALLLOG_004(self, mock_get_values, mock_get_contact):
        """
        TC_CALLLOG_004: Định dạng call loại Incoming,
        gán activity_type, _caller và _receiver đúng.
        """
        mock_get_contact.return_value = {'full_name': 'Nguyen Van A', 'image': 'avatarA.png'}
        mock_get_values.return_value = [('User B', 'avatarB.png')]
        call_data = {
            'type': 'Incoming',
            'duration': 83,
            'from': '+841234',
            'receiver': 'userb@example.com'
        }
        parsed = parse_call_log(call_data.copy())
        # Kiểm tra duration và flag
        self.assertEqual(parsed['_duration'], '00:01:23')
        self.assertFalse(parsed['show_recording'])
        self.assertEqual(parsed['activity_type'], 'incoming_call')
        # Kiểm tra thông tin caller và receiver
        self.assertEqual(parsed['_caller']['label'], 'Nguyen Van A')
        self.assertEqual(parsed['_caller']['image'], 'avatarA.png')
        self.assertEqual(parsed['_receiver']['label'], 'User B')
        self.assertEqual(parsed['_receiver']['image'], 'avatarB.png')

    @patch('crm.fcrm.doctype.crm_call_log.crm_call_log.get_contact_by_phone_number')
    @patch('frappe.db.get_values')
    def test_parse_call_log_outgoing_TC_CALLLOG_005(self, mock_get_values, mock_get_contact):
        """
        TC_CALLLOG_005: Định dạng call loại Outgoing,
        gán activity_type, _caller và _receiver đúng.
        """
        mock_get_contact.return_value = {'full_name': 'Tran Thi C', 'image': None}
        mock_get_values.return_value = [('User D', 'avatarD.png')]
        call_data = {
            'type': 'Outgoing',
            'duration': 45,
            'to': '+849876',
            'caller': 'userd@example.com'
        }
        parsed = parse_call_log(call_data.copy())
        self.assertEqual(parsed['activity_type'], 'outgoing_call')
        self.assertEqual(parsed['_duration'], '00:01:23')
        self.assertEqual(parsed['_caller']['label'], 'User D')
        self.assertEqual(parsed['_caller']['image'], 'avatarD.png')
        self.assertEqual(parsed['_receiver']['label'], 'Tran Thi C')
        self.assertIsNone(parsed['_receiver']['image'])

    def test_parse_call_log_unknown_type_TC_CALLLOG_006(self):
        """
        TC_CALLLOG_006: Call không có type hoặc type lạ,
        vẫn set _duration và show_recording,
        không tạo activity_type, _caller, _receiver.
        """
        call_data = {'duration': 10}
        parsed = parse_call_log(call_data.copy())
        self.assertEqual(parsed['_duration'], '00:01:23')
        self.assertFalse(parsed['show_recording'])
        self.assertNotIn('activity_type', parsed)
        self.assertNotIn('_caller', parsed)
        self.assertNotIn('_receiver', parsed)

    @patch('frappe.get_cached_doc')
    @patch('crm.fcrm.doctype.crm_call_log.crm_call_log.parse_call_log')
    def test_get_call_log_full_TC_CALLLOG_007(self, mock_parse, mock_get_cached):
        """
        TC_CALLLOG_007: get_call_log phải gom note, task,
        và mapping reference_doctype đúng.
        """
        # Dữ liệu mẫu bao gồm link tới CRM Task và FCRM Note
        base = {
            'name': 'CALL-1',
            'caller': 'u1',
            'receiver': 'u2',
            'duration': 100,
            'type': 'Incoming',
            'status': 'Completed',
            'from': '+841111',
            'to': '+842222',
            'note': 'NOTE-1',
            'reference_doctype': 'CRM Deal',
            'reference_docname': 'DEAL-1',
            'creation': '2025-04-17T12:00:00',
            'links': [
                {'link_doctype': 'CRM Task', 'link_name': 'TASK-1'},
                {'link_doctype': 'FCRM Note', 'link_name': 'NOTE-2'}
            ]
        }
        # mock parse_call_log trả về base
        mock_parse.return_value = base.copy()
        # Tạo fake docs: note đầu tiên, task, note thứ hai
        fake_call = MagicMock(as_dict=lambda: base.copy())
        fake_note1 = MagicMock(as_dict=lambda: {'content': 'Ghi chú 1'})
        fake_task = MagicMock(as_dict=lambda: {'subject': 'Nhiệm vụ 1'})
        fake_note2 = MagicMock(as_dict=lambda: {'content': 'Ghi chú 2'})
        mock_get_cached.side_effect = [fake_call, fake_note1, fake_task, fake_note2]

        result = get_call_log('CALL-1')
        # Kiểm tra list ghi chú và nhiệm vụ
        self.assertEqual(len(result['_notes']), 2)
        self.assertEqual(result['_notes'][0]['content'], 'Ghi chú 1')
        self.assertEqual(result['_notes'][1]['content'], 'Ghi chú 2')
        self.assertEqual(len(result['_tasks']), 1)
        self.assertEqual(result['_tasks'][0]['subject'], 'Nhiệm vụ 1')
        # Kiểm tra mapping reference_doctype
        self.assertEqual(result['_deal'], 'DEAL-1')

    @patch('frappe.new_doc')
    @patch('frappe.get_doc')
    def test_create_lead_from_call_log_TC_CALLLOG_008(self, mock_get_doc, mock_new_doc):
        """
        TC_CALLLOG_008: create_lead_from_call_log phải tạo Lead mới,
        set đúng first_name, mobile_no, link call log, lưu vào DB.
        """
        input_data = {'name': 'CALL-2', 'from': '+843333'}
        # mock tạo lead
        fake_lead = MagicMock()
        fake_lead.name = 'LEAD-2'
        mock_new_doc.return_value = fake_lead
        # mock get_doc cho call log
        fake_call = MagicMock()
        mock_get_doc.return_value = fake_call

        returned = create_lead_from_call_log(input_data)
        # Kiểm tra đã khởi tạo lead và gán fields
        mock_new_doc.assert_called_with('CRM Lead')
        self.assertEqual(fake_lead.first_name, 'Lead from call +843333')
        self.assertEqual(fake_lead.mobile_no, '+843333')
        # Kiểm tra link và save
        fake_call.link_with_reference_doc.assert_called_with('CRM Lead', 'LEAD-2')
        fake_call.save.assert_called()
        # Phải trả về tên lead mới
        self.assertEqual(returned, 'LEAD-2')
        # Kiểm tra tồn tại trong DB (sẽ rollback sau)
        self.assertTrue(frappe.db.exists('CRM Lead', 'LEAD-2'))
