class BaseGateway:
    """Common interface every payment gateway must implement."""

    name = None

    def create_payment_intent(self, *, amount, currency, order, metadata=None):
        """
        Initializes a payment on the gateway's side.
        Must return a dict: {"reference": str, "client_secret_or_redirect_url": str, "raw_response": dict}
        """
        raise NotImplementedError

    def verify_webhook_signature(self, *, payload_body, headers):
        """Returns True if the webhook signature is valid, else False."""
        raise NotImplementedError

    def parse_webhook_event(self, *, payload_body):
        """
        Returns a normalized dict: {
            "event_id": str, "event_type": str, "gateway_reference": str,
            "status": "succeeded" | "failed" | "pending", "raw": dict
        }
        """
        raise NotImplementedError

    def create_refund(self, *, gateway_reference, amount):
        """Returns a dict: {"reference": str, "status": str, "raw_response": dict}"""
        raise NotImplementedError