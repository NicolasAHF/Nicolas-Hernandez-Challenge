import pytest


@pytest.fixture
def user(client):
    return client.post("/users", json={"name": "Alice"}).json()


def test_create_plan(client, user):
    response = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn Python", "hours_per_week": 10.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["goal"] == "Learn Python"
    assert data["user_id"] == user["id"]
    assert isinstance(data["id"], int)


def test_create_plan_defaults_description_and_target_date_to_null(client, user):
    response = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn Python", "hours_per_week": 10.0},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] is None
    assert data["target_date"] is None


def test_create_plan_with_description_and_target_date(client, user):
    response = client.post(
        "/plans",
        json={
            "user_id": user["id"],
            "goal": "Learn FastAPI",
            "hours_per_week": 5.0,
            "description": "Focus on auth and testing",
            "target_date": "2026-06-01",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Focus on auth and testing"
    assert data["target_date"] == "2026-06-01"


def test_get_plan(client, user):
    created = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn Python", "hours_per_week": 10.0},
    ).json()
    response = client.get(f"/plans/{created['id']}")
    assert response.status_code == 200
    assert response.json()["goal"] == "Learn Python"


def test_get_plan_not_found(client):
    response = client.get("/plans/999")
    assert response.status_code == 404


def test_get_user_plans(client, user):
    client.post(
        "/plans", json={"user_id": user["id"], "goal": "Goal A", "hours_per_week": 5.0}
    )
    client.post(
        "/plans", json={"user_id": user["id"], "goal": "Goal B", "hours_per_week": 3.0}
    )
    response = client.get(f"/users/{user['id']}/plans")
    assert response.status_code == 200
    plans = response.json()
    assert len(plans) == 2
    assert {p["goal"] for p in plans} == {"Goal A", "Goal B"}


def test_create_plan_user_not_found(client):
    response = client.post(
        "/plans",
        json={"user_id": 999, "goal": "Orphan plan", "hours_per_week": 1.0},
    )
    assert response.status_code == 404


def test_update_plan(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn Python", "hours_per_week": 10.0},
    ).json()
    response = client.patch(
        f"/plans/{plan['id']}",
        json={"description": "Updated notes", "target_date": "2026-09-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated notes"
    assert data["target_date"] == "2026-09-01"
    assert data["goal"] == "Learn Python"


def test_update_plan_not_found(client):
    response = client.patch("/plans/999", json={"description": "x"})
    assert response.status_code == 404


def _add_task(client, plan_id, title, hours, completed=False):
    task = client.post(
        f"/plans/{plan_id}/tasks",
        json={"title": title, "estimated_hours": hours},
    ).json()
    if completed:
        client.patch(
            f"/plans/{plan_id}/tasks/{task['id']}", json={"completed": True}
        )
    return task


def test_plan_metrics(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Learn Python", "hours_per_week": 10.0},
    ).json()
    _add_task(client, plan["id"], "Task A", 4.0, completed=True)
    _add_task(client, plan["id"], "Task B", 6.0, completed=False)
    _add_task(client, plan["id"], "Task C", 2.0, completed=True)

    response = client.get(f"/plans/{plan['id']}/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 3,
        "completed_tasks": 2,
        "completion_percentage": 67,  # round(2/3 * 100)
        "total_estimated_hours": 12.0,
        "completed_hours": 6.0,
    }


def test_plan_metrics_all_completed(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Goal", "hours_per_week": 5.0},
    ).json()
    _add_task(client, plan["id"], "Only task", 3.0, completed=True)

    response = client.get(f"/plans/{plan['id']}/metrics")

    assert response.status_code == 200
    assert response.json()["completion_percentage"] == 100
    assert response.json()["completed_hours"] == 3.0


def test_plan_metrics_no_tasks(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Empty plan", "hours_per_week": 5.0},
    ).json()

    response = client.get(f"/plans/{plan['id']}/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "total_tasks": 0,
        "completed_tasks": 0,
        "completion_percentage": 0,
        "total_estimated_hours": 0.0,
        "completed_hours": 0.0,
    }


def test_plan_metrics_not_found(client):
    response = client.get("/plans/999/metrics")
    assert response.status_code == 404


def test_plan_rebalance_overloaded_schedules_whole_tasks_across_weeks(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Heavy plan", "hours_per_week": 10.0},
    ).json()
    t1 = _add_task(client, plan["id"], "Task A", 6.0)
    t2 = _add_task(client, plan["id"], "Task B", 4.0)
    t3 = _add_task(client, plan["id"], "Task C", 10.0)

    response = client.get(f"/plans/{plan['id']}/rebalance")

    assert response.status_code == 200
    assert response.json() == {
        "overloaded": True,
        "hours_per_week": 10.0,
        "total_estimated_hours": 20.0,
        "weeks_needed": 2,
        "schedule": [
            {
                "week": 1,
                "tasks": [
                    {"task_id": t1["id"], "title": "Task A", "hours": 6.0},
                    {"task_id": t2["id"], "title": "Task B", "hours": 4.0},
                ],
                "total_hours": 10.0,
            },
            {
                "week": 2,
                "tasks": [{"task_id": t3["id"], "title": "Task C", "hours": 10.0}],
                "total_hours": 10.0,
            },
        ],
    }


def test_plan_rebalance_splits_task_larger_than_weekly_budget(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Big task", "hours_per_week": 10.0},
    ).json()
    t = _add_task(client, plan["id"], "Huge task", 25.0)

    response = client.get(f"/plans/{plan['id']}/rebalance")

    assert response.status_code == 200
    assert response.json() == {
        "overloaded": True,
        "hours_per_week": 10.0,
        "total_estimated_hours": 25.0,
        "weeks_needed": 3,
        "schedule": [
            {
                "week": 1,
                "tasks": [{"task_id": t["id"], "title": "Huge task -1", "hours": 10.0}],
                "total_hours": 10.0,
            },
            {
                "week": 2,
                "tasks": [{"task_id": t["id"], "title": "Huge task -2", "hours": 10.0}],
                "total_hours": 10.0,
            },
            {
                "week": 3,
                "tasks": [{"task_id": t["id"], "title": "Huge task -3", "hours": 5.0}],
                "total_hours": 5.0,
            },
        ],
    }


def test_plan_rebalance_split_remainder_shares_week_with_next_task(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Mixed", "hours_per_week": 10.0},
    ).json()
    big = _add_task(client, plan["id"], "Big", 12.0)
    small = _add_task(client, plan["id"], "Small", 3.0)

    response = client.get(f"/plans/{plan['id']}/rebalance")

    assert response.json()["schedule"] == [
        {
            "week": 1,
            "tasks": [{"task_id": big["id"], "title": "Big -1", "hours": 10.0}],
            "total_hours": 10.0,
        },
        {
            "week": 2,
            "tasks": [
                {"task_id": big["id"], "title": "Big -2", "hours": 2.0},
                {"task_id": small["id"], "title": "Small", "hours": 3.0},
            ],
            "total_hours": 5.0,
        },
    ]


def test_plan_rebalance_not_overloaded(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Light plan", "hours_per_week": 10.0},
    ).json()
    _add_task(client, plan["id"], "Task A", 3.0)
    _add_task(client, plan["id"], "Task B", 4.0)

    response = client.get(f"/plans/{plan['id']}/rebalance")

    assert response.status_code == 200
    body = response.json()
    assert body["overloaded"] is False
    assert body["weeks_needed"] == 1
    assert body["schedule"] == []


def test_plan_rebalance_no_tasks(client, user):
    plan = client.post(
        "/plans",
        json={"user_id": user["id"], "goal": "Empty plan", "hours_per_week": 5.0},
    ).json()

    response = client.get(f"/plans/{plan['id']}/rebalance")

    assert response.status_code == 200
    body = response.json()
    assert body["overloaded"] is False
    assert body["weeks_needed"] == 0
    assert body["schedule"] == []


def test_plan_rebalance_not_found(client):
    response = client.get("/plans/999/rebalance")
    assert response.status_code == 404
