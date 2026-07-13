import uuid
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor
from redis import Redis

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(autouse=True)
def ensure_redis_up():
    r = Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
    try:
        r.ping()
    except Exception:
        pytest.skip("Redis unreachable — infra issue, not a rate-limit bug")


def hit_endpoint(path: str, user_id: str):
    headers = {"X-User-ID": user_id}
    try:
        response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=5)
        return response.status_code
    except Exception as e:
        pytest.fail(f"Request failed, not a rate-limit result: {e}")


@pytest.mark.parametrize("path, limit", [
    ("/api/data", 5),
    ("/api/sliding-data", 5),
    ("/api/token-bucket-data", 5),
])
def test_concurrent_race_condition(path, limit):
    user_id = f"stress_test_{uuid.uuid4()}"
    num_threads = 50

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(hit_endpoint, path, user_id) for _ in range(num_threads)]
        results = [f.result() for f in futures]

    success_count = results.count(200)
    blocked_count = results.count(429)
    assert success_count == limit, f"RACE CONDITION: {success_count} succeeded, expected {limit}"
    assert blocked_count == num_threads - limit