"""Models used by the WeBirr Python SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, TypeVar

T = TypeVar("T")


def _lookup(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def _to_dict(data: Any) -> dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    return vars(data)


@dataclass
class ApiResponse(Generic[T]):
    """Common WeBirr API response wrapper."""

    error: str | None = None
    res: T | None = None
    error_code: str | None = None

    @property
    def errorCode(self) -> str | None:
        """Gateway-style alias for callers that prefer the wire name."""

        return self.error_code

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        res_factory: Callable[[Any], T] | None = None,
    ) -> "ApiResponse[T]":
        raw_res = data.get("res")
        res = res_factory(raw_res) if res_factory and raw_res is not None else raw_res
        return cls(
            error=data.get("error"),
            res=res,
            error_code=data.get("errorCode") or data.get("error_code"),
        )


@dataclass
class Bill:
    """Create/update request model for WeBirr bills."""

    amount: str = ""
    customer_code: str = ""
    customer_name: str = ""
    customer_phone: str = ""
    time: str = ""
    description: str = ""
    bill_reference: str = ""
    merchant_id: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "customerCode": self.customer_code,
            "customerName": self.customer_name,
            "customerPhone": self.customer_phone,
            "time": self.time,
            "description": self.description,
            "billReference": self.bill_reference,
            "merchantID": self.merchant_id,
            "extras": self.extras or {},
        }

    @classmethod
    def from_dict(cls, data: Any) -> "Bill":
        source = _to_dict(data)
        return cls(
            amount=str(_lookup(source, "amount")),
            customer_code=str(_lookup(source, "customerCode", "customer_code")),
            customer_name=str(_lookup(source, "customerName", "customer_name")),
            customer_phone=str(_lookup(source, "customerPhone", "customer_phone")),
            time=str(_lookup(source, "time")),
            description=str(_lookup(source, "description")),
            bill_reference=str(_lookup(source, "billReference", "bill_reference")),
            merchant_id=str(_lookup(source, "merchantID", "merchant_id")),
            extras=dict(_lookup(source, "extras", default={}) or {}),
        )


@dataclass
class BillResponse(Bill):
    """Bill retrieval/list response model."""

    wbc_code: str = ""
    payment_status: int | None = None
    update_time_stamp: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "BillResponse":
        source = _to_dict(data)
        bill = Bill.from_dict(source)
        return cls(
            **bill.__dict__,
            wbc_code=str(_lookup(source, "wbcCode", "wbc_code")),
            payment_status=_lookup(source, "paymentStatus", "payment_status", default=None),
            update_time_stamp=str(_lookup(source, "updateTimeStamp", "update_time_stamp")),
        )

    @property
    def wbcCode(self) -> str:
        return self.wbc_code

    @property
    def paymentStatus(self) -> int | None:
        return self.payment_status

    @property
    def updateTimeStamp(self) -> str:
        return self.update_time_stamp


@dataclass
class PaymentDetail:
    """Payment detail returned by single payment status."""

    status: int | None = None
    id: int | str | None = None
    bank_id: str = ""
    payment_reference: str = ""
    payment_date: str = ""
    time: str = ""
    confirmed: bool | None = None
    confirmed_time: str = ""
    amount: str = ""
    wbc_code: str = ""
    update_time_stamp: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "PaymentDetail":
        source = _to_dict(data)
        payment_date = str(_lookup(source, "paymentDate", "payment_date", "time"))
        time = str(_lookup(source, "time", "paymentDate", "payment_date"))
        return cls(
            status=_lookup(source, "status", default=None),
            id=_lookup(source, "id", default=None),
            bank_id=str(_lookup(source, "bankID", "bank_id")),
            payment_reference=str(_lookup(source, "paymentReference", "payment_reference")),
            payment_date=payment_date,
            time=time,
            confirmed=_lookup(source, "confirmed", default=None),
            confirmed_time=str(_lookup(source, "confirmedTime", "confirmed_time")),
            amount=str(_lookup(source, "amount")),
            wbc_code=str(_lookup(source, "wbcCode", "wbc_code")),
            update_time_stamp=str(_lookup(source, "updateTimeStamp", "update_time_stamp")),
        )

    @property
    def bankID(self) -> str:
        return self.bank_id

    @property
    def paymentReference(self) -> str:
        return self.payment_reference

    @property
    def paymentDate(self) -> str:
        return self.payment_date

    @property
    def confirmedTime(self) -> str:
        return self.confirmed_time

    @property
    def wbcCode(self) -> str:
        return self.wbc_code

    @property
    def updateTimeStamp(self) -> str:
        return self.update_time_stamp


@dataclass
class PaymentStatus:
    """Single payment status wrapper."""

    status: int | None = None
    data: PaymentDetail | None = None

    @property
    def is_paid(self) -> bool:
        return self.status == 2

    @classmethod
    def from_dict(cls, data: Any) -> "PaymentStatus":
        source = _to_dict(data)
        raw_data = source.get("data")
        return cls(
            status=_lookup(source, "status", default=None),
            data=PaymentDetail.from_dict(raw_data) if raw_data else None,
        )


@dataclass
class PaymentResponse(PaymentDetail):
    """Payment item returned by bulk polling and webhook payloads."""

    canceled: bool | None = None
    canceled_time: str = ""

    @property
    def is_paid(self) -> bool:
        return self.status == 2

    @property
    def is_reversed(self) -> bool:
        return self.status == 3

    @classmethod
    def from_dict(cls, data: Any) -> "PaymentResponse":
        source = _to_dict(data)
        detail = PaymentDetail.from_dict(source)
        return cls(
            **detail.__dict__,
            canceled=_lookup(source, "canceled", default=None),
            canceled_time=str(_lookup(source, "canceledTime", "canceled_time")),
        )

    @property
    def canceledTime(self) -> str:
        return self.canceled_time


@dataclass
class SupportedBank:
    """Bank enabled for the configured merchant checkout."""

    bank_id: str = ""
    name: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "SupportedBank":
        source = _to_dict(data)
        return cls(
            bank_id=str(_lookup(source, "bankID", "bankid", "bank_id")),
            name=str(_lookup(source, "name", "bankName", "bank_name")),
        )

    @property
    def bankID(self) -> str:
        return self.bank_id


@dataclass
class Stat:
    """Basic statistics for bills and payments."""

    n_bills: int | None = None
    n_bills_paid: int | None = None
    n_bills_unpaid: int | None = None
    amount_bills: str = ""
    amount_paid: str = ""
    amount_unpaid: str = ""

    @classmethod
    def from_dict(cls, data: Any) -> "Stat":
        source = _to_dict(data)
        return cls(
            n_bills=_lookup(source, "NBills", "nBills", "n_bills", default=None),
            n_bills_paid=_lookup(source, "NBillsPaid", "nBillsPaid", "n_bills_paid", default=None),
            n_bills_unpaid=_lookup(source, "NBillsUnpaid", "nBillsUnpaid", "n_bills_unpaid", default=None),
            amount_bills=str(_lookup(source, "AmountBills", "amountBills", "amount_bills")),
            amount_paid=str(_lookup(source, "AmountPaid", "amountPaid", "amount_paid")),
            amount_unpaid=str(_lookup(source, "AmountUnpaid", "amountUnpaid", "amount_unpaid")),
        )

    @property
    def nBills(self) -> int | None:
        return self.n_bills

    @property
    def nBillsPaid(self) -> int | None:
        return self.n_bills_paid

    @property
    def nBillsUnpaid(self) -> int | None:
        return self.n_bills_unpaid

    @property
    def amountBills(self) -> str:
        return self.amount_bills

    @property
    def amountPaid(self) -> str:
        return self.amount_paid

    @property
    def amountUnpaid(self) -> str:
        return self.amount_unpaid


def list_of(factory: Callable[[Any], T]) -> Callable[[Iterable[Any]], list[T]]:
    def parse(items: Iterable[Any]) -> list[T]:
        return [factory(item) for item in items or []]

    return parse
