Official Python Client Library for WeBirr Payment Gateway APIs

This Client Library provides convenient access to WeBirr Payment Gateway APIs from Python Applications.

## Install

```bash
$ pip install webirr
```

For local development from this repository:

```bash
$ pip install -e .
```

## Usage

The library needs to be configured with a *merchant Id* & *API key*. You can get it by contacting [webirr.com](https://webirr.net)

> You can use this library for production or test environments. you will need to set is_test_env=True for test, and False for production apps when creating objects of class WeBirrClient

Examples assume the WeBirr TestEnv and read credentials from environment variables:

```bash
export WEBIRR_TEST_ENV_MERCHANT_ID="YOUR_TEST_MERCHANT_ID"
export WEBIRR_TEST_ENV_API_KEY="YOUR_TEST_API_KEY"
```

Create the client with merchant ID, API key, and environment once. The client automatically sets `Bill.merchant_id` before sending bill create/update requests, so application code and examples should not set `merchant_id` on the bill object.

## Example

The examples below keep the PHP and .NET README flow: create the client, call the API, check `error`, handle the success branch, and print `error_code` on failure.

### Creating a new Bill / Updating an existing Bill on WeBirr Servers

```python
import os
from datetime import datetime

from webirr import Bill, WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)

    bill = Bill()
    bill.amount = "270.90"
    bill.customer_code = "cc01"  # it can be email address or phone number if you dont have customer code
    bill.customer_name = "Elias Haileselassie"
    bill.customer_phone = "0911000000"  # optional; used for SMS notification when enabled for the merchant
    bill.time = "2021-07-22 22:14"  # your bill time, always in this format
    bill.description = "hotel booking"
    bill.bill_reference = "python/example/" + datetime.now().strftime("%Y%m%d%H%M%S")  # your unique reference number

    print("\nCreating Bill...")
    res = api.create_bill(bill)

    if not res.error:
        # success
        payment_code = res.res  # returns paymentcode such as 429 723 975
        print(f"\nPayment Code = {payment_code}")  # we may want to save payment code in local db.
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT_DUP_REF

    # Update existing bill if it is not paid
    bill.amount = "278.00"
    bill.customer_name = "Elias python"
    # bill.bill_reference = "WE CAN NOT CHANGE THIS"

    print("\nUpdating Bill...")
    res = api.update_bill(bill)

    if not res.error:
        # success
        print("\nbill is updated succesfully")  # res.res will be 'OK'  no need to check here!
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT


main()
```

### Getting a Bill and Listing Bills

```python
import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    api = WeBirrClient(merchant_id, api_key, True)

    bill_reference = "YOUR_BILL_REFERENCE"  # BILL_REFERENCE_YOU_SAVED_AFTER_CREATING_A_NEW_BILL
    payment_code = "YOUR_PAYMENT_CODE"  # PAYMENT_CODE_YOU_SAVED_AFTER_CREATING_A_NEW_BILL

    print("\nGetting bill by reference...")
    res = api.get_bill_by_reference(bill_reference)
    if not res.error:
        # success
        print("\nBill found by reference.")
        print(f"\nBill Reference: {res.res.bill_reference}")
        print(f"\nPayment Code: {res.res.wbc_code}")
        print(f"\nAmount: {res.res.amount}")
        print(f"\nPayment Status: {res.res.payment_status}")
        print(f"\nUpdate Timestamp: {res.res.update_time_stamp}")
    else:
        # fail
        print(f"\nError: {res.error}")
        print(f"\nError Code: {res.error_code}")

    print("\nGetting bill by payment code...")
    res = api.get_bill_by_payment_code(payment_code)
    if not res.error:
        # success
        print("\nBill found by payment code.")
        print(f"\nBill Reference: {res.res.bill_reference}")
        print(f"\nPayment Code: {res.res.wbc_code}")
    else:
        # fail
        print(f"\nError: {res.error}")
        print(f"\nError Code: {res.error_code}")

    print("\nListing bills...")
    payment_status = -1  # -1 all, 0 pending, 1 unconfirmed payment, 2 paid.
    last_time_stamp = "20251231"  # Date-only cursor; use "20251231235959" when you need time precision.
    limit = 10

    res = api.get_bills(payment_status, last_time_stamp, limit)
    if not res.error:
        # success
        print(f"\nBills returned: {len(res.res)}")
        for bill in res.res:
            print("\n-----------------------------")
            print(f"\nBill Reference: {bill.bill_reference}")
            print(f"\nPayment Code: {bill.wbc_code}")
            print(f"\nAmount: {bill.amount}")
            print(f"\nPayment Status: {bill.payment_status}")
            print(f"\nUpdate Timestamp: {bill.update_time_stamp}")
    else:
        # fail
        print(f"\nError: {res.error}")
        print(f"\nError Code: {res.error_code}")


main()
```

Timestamp cursors can be date-only (`yyyyMMdd`) or include time (`yyyyMMddHHmmss`). Use empty string only when you intentionally want all history from the beginning.

### Getting Payment status of an existing Bill from WeBirr Servers

```python
import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)
    payment_code = "PAYMENT_CODE_YOU_SAVED_AFTER_CREATING_A_NEW_BILL"

    print("\nGetting Payment Status...")
    res = api.get_payment_status(payment_code)

    if not res.error:
        # success
        if res.res and res.res.is_paid:
            payment = res.res.data
            print("\nbill is paid")
            print("\nbill payment detail")
            print(f"\nBank: {payment.bank_id}")
            print(f"\nBank Reference Number: {payment.payment_reference}")
            print(f"\nAmount Paid: {payment.amount}")
            print(f"\nPayment Date: {payment.payment_date}")
        else:
            print("\nbill is pending payment")
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT


main()
```

*Sample object returned from getPaymentStatus()*

```python
sample = {
    "error": None,
    "res": {
        "status": 2,
        "data": {
            "status": 2,
            "id": 111219507,
            "bankID": "cbe_mobile",
            "paymentReference": "TX70e78862148f4c249606",
            "paymentDate": "2025-02-26 22:17:19",
            "confirmed": True,
            "confirmedTime": "2025-02-26 22:17:19",
            "amount": "278",
            "wbcCode": "149 233 514",
            "updateTimeStamp": "2025022622171981338",
        },
    },
    "errorCode": None,
}
```

Use `payment_date` as the payment time field. `time` remains available as a deprecated backward-compatible alias.

### Deleting an existing Bill from WeBirr Servers (if it is not paid)

```python
import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)
    payment_code = "PAYMENT_CODE_YOU_SAVED_AFTER_CREATING_A_NEW_BILL"

    print("\nDeleting Bill...")
    res = api.delete_bill(payment_code)

    if not res.error:
        # success
        print("\nbill is deleted succesfully")  # res.res will be 'OK'  no need to check here!
    else:
        # fail
        print(f"\nerror: {res.error}")
        print(f"\nerrorCode: {res.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT


main()
```

### Getting list of Payments and process them with Bulk Polling Consumer

```python
import os
import time

from webirr import WeBirrClient


class PaymentProcessor:
    def __init__(self):
        api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
        merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")
        self.api = WeBirrClient(merchant_id, api_key, True)
        self.last_time_stamp = "20251231"  # Example cursor. Save the last processed payment updateTimeStamp in your database.

    def run_once(self):
        print("\nRetrieving Payments...")
        self.fetch_and_process_payments()

    def run_forever(self):
        while True:
            self.run_once()
            print("\nSleeping for 5 seconds...")
            time.sleep(5)

    def fetch_and_process_payments(self):
        limit = 100  # Number of records to retrieve depending on your processing requirement & capacity
        response = self.api.get_payments(self.last_time_stamp, limit)

        if not response.error:
            # success
            if len(response.res) == 0:
                print("\nNo new payments found.")
            for payment in response.res:
                self.process_payment(payment)
                print("\n-----------------------------")

            if len(response.res) > 0:
                self.last_time_stamp = response.res[-1].update_time_stamp
                print(f"\nLast Timestamp: {self.last_time_stamp}")  # save updateTimeStamp to your database for the next get_payments() call
        else:
            # fail
            print(f"\nerror: {response.error}")
            print(f"\nerrorCode: {response.error_code}")  # can be used to handle specific business error such as ERROR_INVALID_INPUT

    def process_payment(self, payment):
        # Process Payment should be implemented as idempotent operation for production use cases.
        # This method and logic can be shared among all payment processing consumers: 1. bulk polling, 2. webhook, 3. single payment polling.
        print(f"\nPayment Status: {payment.status}")
        if payment.is_paid:
            print("\nPayment Status Text: Paid.")
        if payment.is_reversed:
            print("\nPayment Status Text: Reversed.")
        print(f"\nBank: {payment.bank_id}")
        print(f"\nBank Reference Number: {payment.payment_reference}")
        print(f"\nAmount Paid: {payment.amount}")
        print(f"\nPayment Date: {payment.payment_date}")
        print(f"\nReversal/Cancel Date: {payment.canceled_time}")
        print(f"\nUpdate Timestamp: {payment.update_time_stamp}")


PaymentProcessor().run_once()
```

Bulk polling should persist `updateTimeStamp` only after processing the batch successfully. Polling processors should be idempotent because duplicate/redundant reads are possible.

### Webhooks - Payment processing using Webhook Callbacks

```python
import hmac
import json
import os

from webirr import PaymentResponse


class Webhook:
    # Webhook handler for processing payment updates from WeBirr.
    # This endpoint should be hosted on a secure server with HTTPS enabled.
    def handle_request(self, method, provided_auth_key, raw_payload):
        # Validate request method is POST
        if method.upper() != "POST":
            return self.json_response(405, {"error": "Method Not Allowed. POST required."})

        # Authenticate using authKey query string parameter.
        if not self.is_authenticated(provided_auth_key):
            return self.json_response(403, {"error": "Unauthorized access. Invalid authKey."})

        if not raw_payload:
            return self.json_response(400, {"error": "Empty request body."})

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return self.json_response(400, {"error": "Invalid JSON format."})

        payment_data = payload.get("data", payload)
        if not payment_data:
            return self.json_response(400, {"error": "Invalid payment data."})

        payment = PaymentResponse.from_dict(payment_data)
        self.process_payment(payment)

        return self.json_response(200, {"success": True, "message": "Payment received and queued for processing"})

    def is_authenticated(self, provided_auth_key):
        expected_auth_key = os.getenv("WEBIRR_WEBHOOK_AUTH_KEY", "YOUR_WEBHOOK_AUTH_KEY")
        return bool(expected_auth_key) and hmac.compare_digest(expected_auth_key, provided_auth_key or "")

    def process_payment(self, payment):
        # Process Payment should be implemented as idempotent operation for production use cases.
        # This method and logic can be shared among all payment processing consumers: 1. bulk polling, 2. webhook, 3. single payment polling.
        print(f"\nPayment Status: {payment.status}")
        if payment.is_paid:
            print("\nPayment Status Text: Paid.")
        if payment.is_reversed:
            print("\nPayment Status Text: Reversed.")
        print(f"\nBank: {payment.bank_id}")
        print(f"\nBank Reference Number: {payment.payment_reference}")
        print(f"\nAmount Paid: {payment.amount}")
        print(f"\nPayment Date: {payment.payment_date}")
        print(f"\nReversal/Cancel Date: {payment.canceled_time}")
        print(f"\nUpdate Timestamp: {payment.update_time_stamp}")

    def json_response(self, status_code, body):
        return {"status_code": status_code, "content_type": "application/json", "body": json.dumps(body)}


# Once hosted, the webhook URL needs to be shared with WeBirr for configuration.
```

### Gettting basic Statistics about bills created and payments received for a date range

```python
import os

from webirr import WeBirrClient


def main():
    api_key = os.getenv("WEBIRR_TEST_ENV_API_KEY", "")
    merchant_id = os.getenv("WEBIRR_TEST_ENV_MERCHANT_ID", "")

    # api_key = "YOUR_API_KEY"
    # merchant_id = "YOUR_MERCHANT_ID"

    api = WeBirrClient(merchant_id, api_key, True)

    date_from = "2025-01-01"  # YYYY-MM-DD
    date_to = "2030-01-31"  # YYYY-MM-DD

    print("\nRetrieving Statistics...")
    print(f"\nDate From: {date_from}")
    print(f"\nDate To: {date_to}")

    response = api.get_stat(date_from, date_to)

    if not response.error:
        # success
        stat = response.res
        print(f"\nNumber of Bills Created: {stat.n_bills}")
        print(f"\nNumber of Paid Bills: {stat.n_bills_paid}")
        print(f"\nNumber of Unpaid Bills: {stat.n_bills_unpaid}")
        print(f"\nAmount of Bills: {stat.amount_bills}")
        print(f"\nAmount Paid: {stat.amount_paid}")
        print(f"\nAmount Unpaid: {stat.amount_unpaid}")
    else:
        # fail
        print(f"\nError: {response.error}")
        print(f"\nError Code: {response.error_code}")


main()
```

## Examples

The `examples` directory includes separate workflows matching the PHP SDK examples:

```bash
python examples/example1_create_update_bill.py
python examples/example2_payment_status_single_poll.py
python examples/example3_delete_bill.py
python examples/example4_payment_status_bulk_poll.py
python examples/example5_stat_report.py
python examples/example6_payment_status_webhook.py
python examples/example7_get_bill_and_list_bills.py
```

## Reusable HTTP Session

For batch or mass bill workloads, pass a configured `requests.Session` so your application can reuse connections, configure adapters, and apply its own retry policy:

```python
import requests

from webirr import WeBirrClient

session = requests.Session()
api = WeBirrClient(merchant_id, api_key, True, session=session)
```

The SDK does not silently retry bill creation. Configure retry behavior in your application so duplicate create/update processing remains under your control.
