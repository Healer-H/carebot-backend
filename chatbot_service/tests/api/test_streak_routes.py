import pytest
from datetime import date
from models.health_streak import HealthActivity, UserStreak, StreakCompletion

# ---------- Fixtures ----------

@pytest.fixture
def test_activity(db):
    activity = HealthActivity(
        name="Drink Water",
        description="Drink 8 cups of water",
        difficulty='easy'
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@pytest.fixture
def test_streak(db, test_user, test_activity):
    streak = UserStreak(
        user_id=test_user.id,
        activity_id=test_activity.id,
        current_streak=0,
        longest_streak=0,
        last_completed=None
    )
    db.add(streak)
    db.commit()
    db.refresh(streak)
    return streak


# ---------- Tests ----------

def test_create_streak(client, auth_header, test_activity):
    res = client.get(f"/streaks/{test_activity.id}", headers=auth_header)
    assert res.status_code == 200
    data = res.json()
    assert data["activity"]["id"] == test_activity.id
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1


def test_get_streaks(client, auth_header, test_streak):
    res = client.get("/streaks", headers=auth_header)
    assert res.status_code == 200
    data = res.json()
    assert any(s["id"] == test_streak.id for s in data)


def test_complete_streak(client, auth_header, test_streak):
    payload = {
        "activity_id": test_streak.activity_id,
        "completed_date": str(date.today())
    }
    res = client.post("/streaks/completions", headers=auth_header, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["activity_id"] == test_streak.activity_id
    assert data["completed_date"] == payload["completed_date"]


def test_complete_streak_twice_same_day(client, auth_header, test_streak):
    payload = {
        "activity_id": test_streak.activity_id,
        "completed_date": str(date.today())
    }
    first = client.post("/streaks/completions", headers=auth_header, json=payload)
    assert first.status_code == 201

    second = client.post("/streaks/completions", headers=auth_header, json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Already completed for today"


def test_get_history(client, auth_header, test_streak, test_user, db):
    completion = StreakCompletion(
        user_id=test_user.id,
        activity_id=test_streak.activity_id,
        completed_date=date.today()
    )
    db.add(completion)
    db.commit()

    res = client.get("/streaks/completions", headers=auth_header, params={})
    print(res.status_code)
    print(res.json())

    assert res.status_code == 200
    data = res.json()
    assert any(item["activity_id"] == test_streak.activity_id for item in data)

def test_get_stats(client, auth_header, test_streak, test_user, db):
    completion = StreakCompletion(
        user_id=test_user.id,
        activity_id=test_streak.activity_id,
        completed_date=date.today()
    )
    db.add(completion)
    db.commit()

    res = client.get("/streaks/stats", headers=auth_header, params={"days": 7})
    assert res.status_code == 200
    data = res.json()

    assert "total_completions" in data
    assert "by_date" in data
    assert "by_activity" in data
    assert "days_with_completions" in data
    assert "period_days" in data
