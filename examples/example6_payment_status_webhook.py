import hmac
import json
import os

from webirr import PaymentResponse


class Webhook:
    """Webhook handler for processing payment updates from WeBirr."""

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
        return {
            "status_code": status_code,
            "content_type": "application/json",
            "body": json.dumps(body),
        }


# Once hosted, the webhook URL needs to be shared with WeBirr for configuration.
