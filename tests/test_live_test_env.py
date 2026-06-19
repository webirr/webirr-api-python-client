import os
import re
import time
import unittest
import uuid
from datetime import datetime, timedelta

from webirr import Bill, WeBirrClient


def test_env_configured():
    return bool(os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID") and os.getenv("WEBIRR_TEST_ENV_API_KEY"))


@unittest.skipUnless(
    test_env_configured(),
    "Set WEBIRR_TEST_ENV_MERCHANT_ID and WEBIRR_TEST_ENV_API_KEY to run live TestEnv smoke tests.",
)
class LiveTestEnvSmokeTests(unittest.TestCase):
    CREATED_AMOUNT = "270.90"
    UPDATED_AMOUNT = "278.00"
    CUSTOMER_CODE = "sdk-test-customer"
    CREATED_CUSTOMER_NAME = "SDK Test Customer"
    UPDATED_CUSTOMER_NAME = "SDK Test Customer Updated"
    CUSTOMER_PHONE = "0911000000"
    DESCRIPTION = "SDK Test Bill"

    @classmethod
    def setUpClass(cls):
        cls.merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")
        cls.api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
        cls.api = WeBirrClient(cls.merchant_id, cls.api_key, True)
        cls.bill_reference = f"python/test/{uuid.uuid4()}"
        cls.payment_code = ""
        cls.bill_update_time_stamp = ""
        cls.deleted = False

    @classmethod
    def tearDownClass(cls):
        if cls.payment_code and not cls.deleted:
            cls.api.delete_bill(cls.payment_code)

    def test_00_get_supported_banks(self):
        response = self.api.get_supported_banks()

        self.assert_no_api_error(response, "GetSupportedBanks")
        self.assertIsInstance(response.res, list)
        self.assertGreater(len(response.res), 0)
        for bank in response.res:
            self.assertTrue(bank.bank_id)
            self.assertTrue(bank.name)

    def test_01_create_bill_without_manual_merchant_id(self):
        bill = self.sample_bill()

        response = self.api.create_bill(bill)

        self.assert_no_api_error(response, "CreateBill")
        self.assertEqual(self.merchant_id, bill.merchant_id)
        self.__class__.payment_code = str(response.res)
        self.assertRegex(self.payment_code, re.compile(r"^\d{3}\s\d{3}\s\d{3}$"))

    def test_02_update_bill_without_manual_merchant_id(self):
        bill = self.sample_bill()
        bill.amount = self.UPDATED_AMOUNT
        bill.customer_name = self.UPDATED_CUSTOMER_NAME

        response = self.api.update_bill(bill)

        self.assert_no_api_error(response, "UpdateBill")
        self.assertEqual(self.merchant_id, bill.merchant_id)
        self.assertEqual("ok", str(response.res).lower())

    def test_03_get_payment_status(self):
        response = self.api.get_payment_status(self.payment_code)

        self.assert_no_api_error(response, "GetPaymentStatus")
        self.assertEqual(0, response.res.status)
        self.assertIsNone(response.res.data)

    def test_04_get_bill_by_reference(self):
        response = self.api.get_bill_by_reference(self.bill_reference)

        self.assert_no_api_error(response, "GetBillByReference")
        self.assert_bill_matches_expected(response.res)
        self.__class__.bill_update_time_stamp = response.res.update_time_stamp

    def test_05_get_bill_by_payment_code(self):
        response = self.api.get_bill_by_payment_code(self.payment_code)

        self.assert_no_api_error(response, "GetBillByPaymentCode")
        self.assert_bill_matches_expected(response.res)

    def test_06_get_bills(self):
        cursor = self.cursor_before(self.bill_update_time_stamp)

        response = self.api.get_bills(0, cursor, 100)

        self.assert_no_api_error(response, "GetBills")
        bill = next((item for item in response.res if item.bill_reference == self.bill_reference), None)
        self.assertIsNotNone(bill, "Bill list should include the bill created by this test run.")
        self.assert_bill_matches_expected(bill)

    def test_07_get_payments(self):
        response = self.api.get_payments("20251231", 10)

        self.assert_no_api_error(response, "GetPayments")
        self.assertIsInstance(response.res, list)

    def test_08_get_stat(self):
        response = self.api.get_stat("2025-01-01", "2030-01-31")

        self.assert_no_api_error(response, "GetStat")
        self.assertIsNotNone(response.res)

    def test_09_delete_bill(self):
        response = self.api.delete_bill(self.payment_code)

        self.assert_no_api_error(response, "DeleteBill")
        self.assertEqual("ok", str(response.res).lower())
        self.__class__.deleted = True

        time.sleep(1)
        deleted_bill = self.api.get_bill_by_reference(self.bill_reference)
        self.assert_api_error(deleted_bill, "Deleted bill should not be returned by reference lookup.")

    def sample_bill(self):
        return Bill(
            amount=self.CREATED_AMOUNT,
            customer_code=self.CUSTOMER_CODE,
            customer_name=self.CREATED_CUSTOMER_NAME,
            customer_phone=self.CUSTOMER_PHONE,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            description=self.DESCRIPTION,
            bill_reference=self.bill_reference,
        )

    def assert_bill_matches_expected(self, bill):
        self.assertEqual(self.bill_reference, bill.bill_reference)
        self.assertEqual(self.merchant_id, bill.merchant_id)
        self.assertEqual(self.CUSTOMER_CODE.upper(), bill.customer_code)
        self.assertEqual(self.UPDATED_CUSTOMER_NAME, bill.customer_name)
        self.assertEqual(self.CUSTOMER_PHONE, bill.customer_phone)
        self.assertEqual(self.DESCRIPTION, bill.description)
        self.assertEqual(0, bill.payment_status)
        self.assertEqual(self.normalize_payment_code(self.payment_code), self.normalize_payment_code(bill.wbc_code))
        self.assertAlmostEqual(float(self.UPDATED_AMOUNT), float(bill.amount), places=2)
        self.assertTrue(bill.update_time_stamp)

    def assert_no_api_error(self, response, operation):
        self.assertIsNone(response.error, f"{operation} error: {response.error}")

    def assert_api_error(self, response, operation):
        self.assertTrue(response.error or response.error_code, operation)

    def normalize_payment_code(self, payment_code):
        return re.sub(r"\D+", "", payment_code)

    def cursor_before(self, update_time_stamp):
        try:
            timestamp = datetime.strptime(update_time_stamp[:14], "%Y%m%d%H%M%S")
        except ValueError:
            return ""
        return (timestamp - timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")


if __name__ == "__main__":
    unittest.main()
