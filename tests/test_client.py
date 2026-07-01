import json
import unittest
from unittest.mock import patch

import requests

from webirr import (
    ApiResponse,
    Bill,
    BillResponse,
    PaymentDetail,
    PaymentResponse,
    PaymentStatus,
    Stat,
    SupportedBank,
    WeBirrClient,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, reason="OK"):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"error": None, "res": "OK", "errorCode": None}
        self.reason = reason

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def raise_for_status(self):
        if 200 <= self.status_code < 300:
            return
        raise requests.HTTPError(f"{self.status_code} {self.reason}".strip(), response=self)


class FakeSession:
    def __init__(self, response=None, responses=None, exception=None):
        self.response = response or FakeResponse()
        self.responses = list(responses or [])
        self.exception = exception
        self.requests = []
        self.headers = {}

    def request(self, method, url, params=None, json=None, timeout=None):
        if self.exception:
            raise self.exception
        self.requests.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "json": json,
                "timeout": timeout,
            }
        )
        if self.responses:
            return self.responses.pop(0)
        return self.response


class WeBirrClientTests(unittest.TestCase):
    def test_uses_default_test_and_production_base_urls(self):
        test_session = FakeSession()
        prod_session = FakeSession()

        WeBirrClient("merchant-from-client", "api-key", True, session=test_session).delete_bill("123")
        WeBirrClient("merchant-from-client", "api-key", False, session=prod_session).delete_bill("123")

        self.assertEqual("https://api.webirr.dev/einvoice/api/bill", test_session.requests[0]["url"])
        self.assertEqual("https://api.webirr.net:8080/einvoice/api/bill", prod_session.requests[0]["url"])

    def test_can_use_injected_session_for_requests(self):
        session = FakeSession()
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        response = client.delete_bill("123 456 789")

        self.assertIsNone(response.error)
        self.assertEqual("OK", response.res)
        self.assertEqual(1, len(session.requests))
        self.assertEqual("DELETE", session.requests[0]["method"])
        self.assertEqual("https://api.webirr.dev/einvoice/api/bill", session.requests[0]["url"])
        self.assertEqual("merchant-from-client", session.requests[0]["params"]["merchant_id"])
        self.assertEqual("123 456 789", session.requests[0]["params"]["wbc_code"])

    def test_testenv_can_use_internal_gateway_url_override(self):
        session = FakeSession()
        with patch.dict("os.environ", {"GATEWAY_URL": "https://local-gateway.example/"}, clear=False):
            WeBirrClient("merchant-from-client", "x", True, session=session).delete_bill("123")

        self.assertEqual("https://local-gateway.example/einvoice/api/bill", session.requests[0]["url"])

    def test_production_ignores_internal_gateway_url_override(self):
        session = FakeSession()
        with patch.dict("os.environ", {"GATEWAY_URL": "https://local-gateway.example/"}, clear=False):
            WeBirrClient("merchant-from-client", "x", False, session=session).delete_bill("123")

        self.assertEqual("https://api.webirr.net:8080/einvoice/api/bill", session.requests[0]["url"])

    def test_create_bill_sets_client_merchant_id_before_sending(self):
        session = FakeSession()
        client = WeBirrClient("merchant-from-client", "x", True, session=session)
        bill = sample_bill()

        client.create_bill(bill)

        self.assertEqual("merchant-from-client", bill.merchant_id)
        self.assertEqual("merchant-from-client", session.requests[0]["json"]["merchantID"])

    def test_empty_client_merchant_id_does_not_overwrite_existing_bill_merchant_id(self):
        session = FakeSession()
        client = WeBirrClient("", "x", True, session=session)
        bill = sample_bill()
        bill.merchant_id = "merchant-on-bill"

        client.create_bill(bill)

        self.assertEqual("merchant-on-bill", bill.merchant_id)
        self.assertEqual("merchant-on-bill", session.requests[0]["json"]["merchantID"])

    def test_query_includes_merchant_id_for_all_endpoints_when_configured(self):
        session = FakeSession(responses=endpoint_responses())
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        exercise_all_endpoints(client)

        self.assertGreaterEqual(len(session.requests), 10)
        for request in session.requests:
            self.assertEqual("merchant-from-client", request["params"]["merchant_id"], request)

    def test_query_omits_empty_merchant_id_for_all_endpoints(self):
        session = FakeSession(responses=endpoint_responses())
        client = WeBirrClient("", "x", True, session=session)

        exercise_all_endpoints(client)

        for request in session.requests:
            self.assertNotIn("merchant_id", request["params"], request)

    def test_endpoint_methods_use_current_gateway_routes(self):
        session = FakeSession(responses=endpoint_responses())
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        exercise_all_endpoints(client)

        observed = [(request["method"], request["url"].replace(client.base_url + "/", "")) for request in session.requests]
        self.assertEqual(
            [
                ("POST", "einvoice/api/bill"),
                ("PUT", "einvoice/api/bill"),
                ("DELETE", "einvoice/api/bill"),
                ("GET", "einvoice/api/paymentStatus"),
                ("GET", "einvoice/api/bill"),
                ("GET", "einvoice/api/bill"),
                ("GET", "einvoice/api/bills"),
                ("GET", "einvoice/api/payments"),
                ("GET", "merchant/stat"),
                ("GET", "einvoice/api/banks"),
            ],
            observed,
        )

    def test_bill_serializes_customer_phone_and_empty_extras_as_object(self):
        bill = sample_bill()

        payload = bill.to_dict()

        self.assertEqual("0911000000", payload["customerPhone"])
        self.assertEqual({}, payload["extras"])
        self.assertEqual("python/unit/1", payload["billReference"])

    def test_bill_serializes_missing_customer_phone_as_empty_string(self):
        bill = sample_bill()
        bill.customer_phone = ""

        self.assertEqual("", bill.to_dict()["customerPhone"])

    def test_bill_serializes_populated_extras_as_object(self):
        bill = sample_bill()
        bill.extras = {"source": "unit-test"}

        self.assertEqual({"source": "unit-test"}, bill.to_dict()["extras"])

    def test_bill_response_deserializes_retrieval_only_fields(self):
        bill = BillResponse.from_dict(
            {
                "customerCode": "SDK-TEST-CUSTOMER",
                "customerName": "SDK Test Customer",
                "customerPhone": "0911000000",
                "billReference": "python/unit/1",
                "merchantID": "merchant-from-client",
                "amount": "278.00",
                "wbcCode": "123 456 789",
                "paymentStatus": 0,
                "updateTimeStamp": "2026061210000000000",
            }
        )

        self.assertEqual("0911000000", bill.customer_phone)
        self.assertEqual("123 456 789", bill.wbc_code)
        self.assertEqual(0, bill.payment_status)
        self.assertEqual("2026061210000000000", bill.update_time_stamp)

    def test_payment_response_uses_payment_date_as_time_alias(self):
        payment = PaymentResponse.from_dict(
            {
                "status": 2,
                "paymentDate": "2026-06-12 10:11:12",
                "amount": "278.00",
                "updateTimeStamp": "2026061210121200000",
            }
        )

        self.assertEqual("2026-06-12 10:11:12", payment.payment_date)
        self.assertEqual(payment.payment_date, payment.time)
        self.assertTrue(payment.is_paid)
        self.assertFalse(payment.is_reversed)

    def test_payment_response_keeps_legacy_time_as_payment_date_alias(self):
        payment = PaymentResponse.from_dict({"status": 3, "time": "2026-06-12 10:11:12"})

        self.assertEqual("2026-06-12 10:11:12", payment.payment_date)
        self.assertEqual(payment.payment_date, payment.time)
        self.assertTrue(payment.is_reversed)

    def test_payment_status_deserializes_payment_detail(self):
        status = PaymentStatus.from_dict(
            {
                "status": 2,
                "data": {
                    "status": 2,
                    "bankID": "test-bank",
                    "paymentReference": "TX-1",
                    "paymentDate": "2026-06-12 10:11:12",
                    "amount": "278.00",
                },
            }
        )

        self.assertTrue(status.is_paid)
        self.assertIsInstance(status.data, PaymentDetail)
        self.assertEqual("test-bank", status.data.bank_id)
        self.assertEqual("2026-06-12 10:11:12", status.data.payment_date)

    def test_stat_deserializes_gateway_pascal_case_fields(self):
        stat = Stat.from_dict(
            {
                "NBills": 4,
                "NBillsPaid": 2,
                "NBillsUnpaid": 2,
                "AmountBills": "100.00",
                "AmountPaid": "50.00",
                "AmountUnpaid": "50.00",
            }
        )

        self.assertEqual(4, stat.n_bills)
        self.assertEqual(2, stat.n_bills_paid)
        self.assertEqual("100.00", stat.amount_bills)

    def test_supported_bank_deserializes_bank_id_wire_field(self):
        bank = SupportedBank.from_dict({"bankID": "cbe_mobile", "name": "CBE Mobile Banking"})

        self.assertEqual("cbe_mobile", bank.bank_id)
        self.assertEqual("cbe_mobile", bank.bankID)
        self.assertEqual("CBE Mobile Banking", bank.name)

    def test_get_supported_banks_returns_typed_bank_list(self):
        session = FakeSession(
            FakeResponse(
                payload={
                    "error": None,
                    "res": [{"bankID": "cbe_mobile", "name": "CBE Mobile Banking"}],
                    "errorCode": None,
                }
            )
        )
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        response = client.get_supported_banks()

        self.assertIsNone(response.error)
        self.assertEqual("cbe_mobile", response.res[0].bank_id)
        self.assertEqual("CBE Mobile Banking", response.res[0].name)

    def test_api_response_uses_error_code_alias(self):
        response = ApiResponse.from_dict({"error": "bad", "errorCode": "ERROR_INVALID_INPUT"})

        self.assertEqual("ERROR_INVALID_INPUT", response.error_code)
        self.assertEqual(response.error_code, response.errorCode)

    def test_request_exception_flows_through_native_channel(self):
        session = FakeSession(exception=requests.Timeout("timed out"))
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        with self.assertRaises(requests.Timeout):
            client.delete_bill("123")

    def test_non_2xx_raises_requests_http_error(self):
        session = FakeSession(FakeResponse(status_code=403, payload={}, reason="Forbidden"))
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        with self.assertRaises(requests.HTTPError) as raised:
            client.delete_bill("123")

        self.assertIs(raised.exception.response, session.response)

    def test_invalid_json_raises_native_exception(self):
        session = FakeSession(FakeResponse(payload=ValueError("bad json")))
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        with self.assertRaises(ValueError):
            client.delete_bill("123")

    def test_non_object_json_raises_type_error(self):
        session = FakeSession(FakeResponse(payload=[]))
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        with self.assertRaises(TypeError):
            client.delete_bill("123")

    def test_2xx_business_error_stays_in_api_response(self):
        session = FakeSession(
            FakeResponse(payload={"error": "bad input", "errorCode": "ERROR_INVALID_INPUT", "res": None})
        )
        client = WeBirrClient("merchant-from-client", "x", True, session=session)

        response = client.delete_bill("123")

        self.assertEqual("bad input", response.error)
        self.assertEqual("ERROR_INVALID_INPUT", response.error_code)


def sample_bill():
    return Bill(
        amount="270.90",
        customer_code="cc01",
        customer_name="Elias Haileselassie",
        customer_phone="0911000000",
        time="2021-07-22 22:14",
        description="hotel booking",
        bill_reference="python/unit/1",
    )


def exercise_all_endpoints(client):
    client.create_bill(sample_bill())
    client.update_bill(sample_bill())
    client.delete_bill("123 456 789")
    client.get_payment_status("123 456 789")
    client.get_bill_by_reference("python/unit/1")
    client.get_bill_by_payment_code("123 456 789")
    client.get_bills(-1, "20251231", 10)
    client.get_payments("20251231", 10)
    client.get_stat("2025-01-01", "2030-01-31")
    client.get_supported_banks()


def endpoint_responses():
    return [
        FakeResponse(payload={"error": None, "res": "123 456 789", "errorCode": None}),
        FakeResponse(payload={"error": None, "res": "OK", "errorCode": None}),
        FakeResponse(payload={"error": None, "res": "OK", "errorCode": None}),
        FakeResponse(payload={"error": None, "res": {"status": 0, "data": None}, "errorCode": None}),
        FakeResponse(payload={"error": None, "res": {"billReference": "python/unit/1"}, "errorCode": None}),
        FakeResponse(payload={"error": None, "res": {"billReference": "python/unit/1"}, "errorCode": None}),
        FakeResponse(payload={"error": None, "res": [{"billReference": "python/unit/1"}], "errorCode": None}),
        FakeResponse(payload={"error": None, "res": [{"paymentDate": "2026-06-12 10:11:12"}], "errorCode": None}),
        FakeResponse(payload={"error": None, "res": {"NBills": 1}, "errorCode": None}),
        FakeResponse(payload={"error": None, "res": [{"bankID": "cbe_mobile", "name": "CBE Mobile Banking"}], "errorCode": None}),
    ]


if __name__ == "__main__":
    unittest.main()
