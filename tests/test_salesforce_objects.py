import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from simple_salesforce import SFType


class SalesforceObjectTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        account = Mock(spec=SFType)
        account.get.return_value = {"Name": "Synthetic account"}
        account.describe.return_value = {"fields": []}
        self.client = SimpleNamespace(Account=account, DisplayName="Synthetic client")
        with patch("simple_salesforce.Salesforce", return_value=self.client):
            from src.salesforce import server
        self.server = server

    async def test_non_object_attributes_are_rejected_by_all_object_tools(self):
        for tool in ("get_object_fields", "get_record", "create_record", "update_record", "delete_record"):
            with self.subTest(tool=tool), patch.object(self.server.sf_client, "sf", self.client):
                with self.assertRaisesRegex(ValueError, "Invalid Salesforce object name"):
                    await self.server.handle_call_tool(
                        tool,
                        {"object_name": "DisplayName", "record_id": "synthetic", "data": {"Name": "Example"}},
                    )

    async def test_valid_object_is_dispatched_to_salesforce_sdk(self):
        with patch.object(self.server.sf_client, "sf", self.client):
            result = await self.server.handle_call_tool(
                "get_record", {"object_name": "Account", "record_id": "synthetic"}
            )
        self.client.Account.get.assert_called_once_with("synthetic")
        self.assertIn("Synthetic account", result[0].text)
