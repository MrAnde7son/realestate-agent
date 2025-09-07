import time
import pytest
from orchestration.data_pipeline import DataPipeline

def get_pipeline():
    # Create DataPipeline instance without triggering __init__ side effects
    return DataPipeline.__new__(DataPipeline)


def test_timeout_triggers_retry_and_raises():
    pipeline = get_pipeline()
    calls = {"count": 0}

    def slow():
        calls["count"] += 1
        time.sleep(0.2)  # always exceeds timeout

    with pytest.raises(TimeoutError):
        pipeline._collect_with_observability(
            "slow", slow, timeout=0.1, retries=1, retry_delay=0
        )
    assert calls["count"] == 2  # initial try + one retry


def test_retry_eventually_succeeds():
    pipeline = get_pipeline()
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] == 1:
            time.sleep(0.2)  # first call times out
        return "ok"

    result = pipeline._collect_with_observability(
        "flaky", flaky, timeout=0.1, retries=1, retry_delay=0
    )
    assert result == "ok"
    assert calls["count"] == 2
