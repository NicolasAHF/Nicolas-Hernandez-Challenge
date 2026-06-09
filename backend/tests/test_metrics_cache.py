import redis
from app.api.deps import get_cache
from app.core.cache import RedisCache, metrics_cache_key
from app.main import app


def _make_plan_with_task(client, hours=4.0):
    user = client.post("/users", json={"name": "Alice"}).json()
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn", "hours_per_week": 10.0},
    ).json()
    task = client.post(
        f"/plans/{plan['id']}/tasks",
        json={"title": "Task", "estimated_hours": hours},
    ).json()
    return plan, task


def test_metrics_served_from_cache(client, cache):
    plan, _ = _make_plan_with_task(client)

    assert client.get(f"/plans/{plan['id']}/metrics").json()["total_tasks"] == 1

    # Poison the cache: if the endpoint reads from the cache, it returns this value.
    cache.set_json(
        metrics_cache_key(plan["id"]),
        {
            "total_tasks": 999,
            "completed_tasks": 0,
            "completion_percentage": 0,
            "total_estimated_hours": 0.0,
            "completed_hours": 0.0,
        },
        300,
    )

    assert client.get(f"/plans/{plan['id']}/metrics").json()["total_tasks"] == 999


def test_cache_invalidated_on_task_create(client):
    plan, _ = _make_plan_with_task(client)

    assert client.get(f"/plans/{plan['id']}/metrics").json()["total_tasks"] == 1

    client.post(
        f"/plans/{plan['id']}/tasks",
        json={"title": "Another", "estimated_hours": 2.0},
    )

    assert client.get(f"/plans/{plan['id']}/metrics").json()["total_tasks"] == 2


def test_cache_invalidated_on_task_toggle(client):
    plan, task = _make_plan_with_task(client)

    assert client.get(f"/plans/{plan['id']}/metrics").json()["completed_tasks"] == 0

    client.patch(
        f"/plans/{plan['id']}/tasks/{task['id']}", json={"completed": True}
    )

    assert client.get(f"/plans/{plan['id']}/metrics").json()["completed_tasks"] == 1


class _BoomClient:
    """Stand-in Redis client that fails on every call (simulates Redis being down)."""

    def get(self, *args, **kwargs):
        raise redis.RedisError("down")

    def set(self, *args, **kwargs):
        raise redis.RedisError("down")

    def delete(self, *args, **kwargs):
        raise redis.RedisError("down")


def test_rediscache_swallows_redis_errors():
    cache = RedisCache(_BoomClient())

    assert cache.get_json("plan:1:metrics") is None
    cache.set_json("plan:1:metrics", {"total_tasks": 1}, 300)
    cache.delete("plan:1:metrics")


def test_metrics_endpoint_survives_redis_down(client):
    app.dependency_overrides[get_cache] = lambda: RedisCache(_BoomClient())
    plan, _ = _make_plan_with_task(client)

    response = client.get(f"/plans/{plan['id']}/metrics")

    assert response.status_code == 200
    assert response.json()["total_tasks"] == 1
