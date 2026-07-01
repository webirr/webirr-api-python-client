"""Platform error helpers for WeBirr SDK retry decisions."""

from __future__ import annotations

import requests


class TransientErrors:
    """Classify platform exceptions that are normally safe to retry."""

    @staticmethod
    def is_transient(error: BaseException) -> bool:
        if isinstance(error, requests.HTTPError):
            response = getattr(error, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code is None:
                return False
            return status_code in (408, 429) or status_code >= 500

        return isinstance(error, (requests.Timeout, requests.ConnectionError))
