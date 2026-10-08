from types import SimpleNamespace
import pytest
from prodcast_manager.worker_policy import POLICY, worker_execution_policy


def test_legacy_release_keeps_its_execution_mode():
    assert worker_execution_policy(None) is None
    assert worker_execution_policy(SimpleNamespace(doc={"management": {}})) is None


def test_new_payload_enables_long_calculations():
    release = SimpleNamespace(doc={"management": {"worker_execution_policy": POLICY}})
    assert worker_execution_policy(release) == POLICY
    assert worker_execution_policy(release) is not POLICY


@pytest.mark.parametrize("change", [{"schema": 2}, {"schema": True}, {"execution_timeout_seconds": True}, {"execution_mode": "unknown"}, {"execution_timeout_seconds": 300}])
def test_unknown_policy_is_rejected(change):
    policy = {**POLICY, **change}
    with pytest.raises(ValueError, match="Unsupported"):
        worker_execution_policy(SimpleNamespace(doc={"management": {"worker_execution_policy": policy}}))
