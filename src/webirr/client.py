"""HTTP client for WeBirr Payment Gateway APIs."""

from __future__ import annotations

import json
import os
from typing import Any, Callable, TypeVar
from urllib.parse import urljoin

import requests

from .models import (
    ApiResponse,
    Bill,
    BillResponse,
    PaymentResponse,
    PaymentStatus,
    Stat,
    SupportedBank,
    list_of,
)

T = TypeVar("T")


class WeBirrClient:
    """Client for WeBirr merchant APIs."""

    TEST_BASE_URL = "https://api.webirr.dev"
    PROD_BASE_URL = "https://api.webirr.net:8080"

    def __init__(
        self,
        merchant_id: str,
        api_key: str,
        is_test_env: bool = True,
        session: requests.Session | None = None,
    ) -> None:
        self.merchant_id = merchant_id or ""
        self.api_key = api_key or ""
        self.base_url = self._resolve_base_url(is_test_env)
        self.session = session or requests.Session()
        self.session.headers.setdefault("Accept", "application/json")

    @classmethod
    def _resolve_base_url(cls, is_test_env: bool) -> str:
        if not is_test_env:
            return cls.PROD_BASE_URL

        gateway_url = os.environ.get("GATEWAY_URL", "").strip()
        if gateway_url:
            return gateway_url.rstrip("/")

        return cls.TEST_BASE_URL

    def create_bill(self, bill: Bill) -> ApiResponse[str]:
        """Create a new bill and return the payment code in ``response.res``."""

        self._prepare_bill(bill)
        return self._send("POST", "einvoice/api/bill", json_body=bill.to_dict())

    def update_bill(self, bill: Bill) -> ApiResponse[str]:
        """Update an existing unpaid bill."""

        self._prepare_bill(bill)
        return self._send("PUT", "einvoice/api/bill", json_body=bill.to_dict())

    def delete_bill(self, payment_code: str) -> ApiResponse[str]:
        """Delete an existing unpaid bill by payment code."""

        return self._send("DELETE", "einvoice/api/bill", params={"wbc_code": payment_code}, json_body={})

    def get_payment_status(self, payment_code: str) -> ApiResponse[PaymentStatus]:
        """Get single payment status by payment code."""

        return self._send(
            "GET",
            "einvoice/api/paymentStatus",
            params={"wbc_code": payment_code},
            res_factory=PaymentStatus.from_dict,
        )

    def get_bill_by_reference(self, bill_reference: str) -> ApiResponse[BillResponse]:
        """Get a bill by merchant bill reference."""

        return self._send(
            "GET",
            "einvoice/api/bill",
            params={"bill_reference": bill_reference},
            res_factory=BillResponse.from_dict,
        )

    def get_bill_by_payment_code(self, payment_code: str) -> ApiResponse[BillResponse]:
        """Get a bill by WeBirr payment code / WBC code."""

        return self._send(
            "GET",
            "einvoice/api/bill",
            params={"wbc_code": payment_code},
            res_factory=BillResponse.from_dict,
        )

    def get_bills(
        self,
        payment_status: int = -1,
        last_time_stamp: str = "",
        limit: int = 100,
    ) -> ApiResponse[list[BillResponse]]:
        """List bills updated after a timestamp cursor."""

        return self._send(
            "GET",
            "einvoice/api/bills",
            params={
                "payment_status": payment_status,
                "last_timestamp": last_time_stamp,
                "limit": limit,
            },
            res_factory=list_of(BillResponse.from_dict),
        )

    def get_payments(
        self,
        last_time_stamp: str = "",
        limit: int = 100,
    ) -> ApiResponse[list[PaymentResponse]]:
        """Poll payment updates after a timestamp cursor."""

        return self._send(
            "GET",
            "einvoice/api/payments",
            params={"last_timestamp": last_time_stamp, "limit": limit},
            res_factory=list_of(PaymentResponse.from_dict),
        )

    def get_stat(self, date_from: str, date_to: str) -> ApiResponse[Stat]:
        """Get basic merchant statistics for a date range."""

        return self._send(
            "GET",
            "merchant/stat",
            params={"date_from": date_from, "date_to": date_to},
            res_factory=Stat.from_dict,
        )

    def get_supported_banks(self) -> ApiResponse[list[SupportedBank]]:
        """Get banks enabled for this merchant checkout."""

        return self._send(
            "GET",
            "einvoice/api/banks",
            res_factory=list_of(SupportedBank.from_dict),
        )

    def _prepare_bill(self, bill: Bill) -> Bill:
        if self.merchant_id:
            bill.merchant_id = self.merchant_id
        return bill

    def _query(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query: dict[str, Any] = {"api_key": self.api_key}
        if self.merchant_id:
            query["merchant_id"] = self.merchant_id
        if params:
            query.update(params)
        return query

    def _send(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        res_factory: Callable[[Any], T] | None = None,
    ) -> ApiResponse[T]:
        url = urljoin(f"{self.base_url}/", path)
        response = self.session.request(
            method,
            url,
            params=self._query(params),
            json=json_body,
            timeout=30,
        )
        return self._decode_response(response, res_factory)

    def _decode_response(
        self,
        response: requests.Response,
        res_factory: Callable[[Any], T] | None = None,
    ) -> ApiResponse[T]:
        if not 200 <= response.status_code < 300:
            reason = getattr(response, "reason", "") or ""
            return ApiResponse(error=f"http error {response.status_code} {reason}".strip())

        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError):
            return ApiResponse(error="invalid json response")

        if not isinstance(payload, dict):
            return ApiResponse(error="invalid response shape")

        return ApiResponse.from_dict(payload, res_factory)
