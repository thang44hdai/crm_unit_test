# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from frappe.tests import IntegrationTestCase, UnitTestCase
import frappe
from frappe import ValidationError
from types import SimpleNamespace

from crm.fcrm.doctype.crm_telephony_agent.crm_telephony_agent import CRMTelephonyAgent

class UnitTestCRMTelephonyAgent(UnitTestCase):
    """
    Unit tests for CRMTelephonyAgent.
    Use this class for testing individual functions and methods.
    """

    class Phone(SimpleNamespace):
        """Mô phỏng dòng child table phone_nos"""
        def get(self, key):
            return getattr(self, key, None)

    def test_set_primary_empty_TC_TELEAGENT_001(self):
        """
        TC_TELEAGENT_001: Nếu không có số điện thoại,
        mobile_no phải là chuỗi rỗng.
        """
        agent = frappe.new_doc("CRM Telephony Agent")
        agent.phone_nos = []
        agent.mobile_no = "nonempty"
        agent.set_primary()
        self.assertEqual(agent.mobile_no, "")

    def test_set_primary_one_primary_TC_TELEAGENT_002(self):
        """
        TC_TELEAGENT_002: Một phone được đánh dấu primary,
        mobile_no phải bằng số đó.
        """
        agent = frappe.new_doc("CRM Telephony Agent")
        phone = self.Phone(number="111111111", is_primary=1)
        agent.phone_nos = [phone]
        agent.mobile_no = ""
        agent.set_primary()
        self.assertEqual(agent.mobile_no, "111111111")

    def test_set_primary_one_non_primary_TC_TELEAGENT_003(self):
        """
        TC_TELEAGENT_003: Một phone không đánh dấu primary,
        mobile_no phải là chuỗi rỗng.
        """
        agent = frappe.new_doc("CRM Telephony Agent")
        phone = self.Phone(number="222222222", is_primary=0)
        agent.phone_nos = [phone]
        agent.mobile_no = "will_be_cleared"
        agent.set_primary()
        self.assertEqual(agent.mobile_no, "")

    def test_set_primary_multiple_primary_TC_TELEAGENT_004(self):
        """
        TC_TELEAGENT_004: Nhiều phone cùng đánh dấu primary,
        trả về ValidationError.
        """
        agent = frappe.new_doc("CRM Telephony Agent")
        p1 = self.Phone(number="333333333", is_primary=1)
        p2 = self.Phone(number="444444444", is_primary=1)
        agent.phone_nos = [p1, p2]
        with self.assertRaises(ValidationError):
            agent.set_primary()

class IntegrationTestCRMTelephonyAgent(IntegrationTestCase):
    """
    Integration tests for CRMTelephonyAgent.
    Use this class for testing interactions between multiple components.
    """
    pass
