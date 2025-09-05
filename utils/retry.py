import time
from typing import Callable, Any

import requests


def request_with_retry(func: Callable[..., requests.Response], *args: Any, max_retries: int = 3, backoff_factor: float = 1.0, **kwargs: Any) -> requests.Response:
    """Call ``func`` with retries and exponential backoff.

    Args:
        func: Callable performing a network request returning ``requests.Response``.
        *args: Positional arguments passed to ``func``.
        max_retries: Maximum number of attempts.
        backoff_factor: Base factor for exponential backoff (sleep = factor * 2**(attempt-1)).
        **kwargs: Keyword arguments passed to ``func``.

    Returns:
        ``requests.Response`` from the successful attempt.

    Raises:
        requests.RequestException: If all attempts fail.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            response = func(*args, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException:
            attempt += 1
            if attempt >= max_retries:
                raise
            sleep_time = backoff_factor * (2 ** (attempt - 1))
            time.sleep(sleep_time)
