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


if __name__ == "__main__":
    PaymentProcessor().run_once()
