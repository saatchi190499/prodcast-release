"""Execution settings supported by the verified Worker payload."""

POLICY = {"schema": 1, "execution_mode": "windows-account", "execution_timeout_seconds": 0}


def worker_execution_policy(release):
    policy = getattr(release, "doc", {}).get("management", {}).get("worker_execution_policy") if release else None
    if policy is None:
        return None
    if policy != POLICY or type(policy.get("schema")) is not int or type(policy.get("execution_timeout_seconds")) is not int:
        raise ValueError("Unsupported Worker execution policy")
    return dict(policy)
