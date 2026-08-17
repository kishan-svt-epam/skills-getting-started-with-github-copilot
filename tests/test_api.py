import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = copy.deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert "michael@mergington.edu" in payload["Chess Club"]["participants"]


def test_signup_for_activity_success(client):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    before_count = len(activities[activity_name]["participants"])

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == before_count + 1


def test_signup_for_activity_duplicate_email_rejected(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}


def test_unregister_for_activity_success(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    before_count = len(activities[activity_name]["participants"])

    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == before_count - 1


def test_unregister_for_activity_missing_email_rejected(client):
    activity_name = "Chess Club"
    email = "missing@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is not signed up for this activity"}


def test_unknown_activity_returns_404_on_signup_and_unregister(client):
    email = "student@mergington.edu"

    signup_response = client.post("/activities/Unknown%20Club/signup?email=student@mergington.edu")
    unregister_response = client.delete(f"/activities/Unknown%20Club/unregister?email={email}")

    assert signup_response.status_code == 404
    assert signup_response.json() == {"detail": "Activity not found"}
    assert unregister_response.status_code == 404
    assert unregister_response.json() == {"detail": "Activity not found"}
