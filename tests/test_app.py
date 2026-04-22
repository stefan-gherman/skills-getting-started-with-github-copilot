"""
FastAPI tests for Mergington High School Activities API
Using AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Monday, 1:00 PM - 2:00 PM",
            "max_participants": 5,
            "participants": []
        }
    }
    
    # Clear existing activities
    activities.clear()
    # Add test activities
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        # Arrange: No special setup needed, activities are pre-populated
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert "Chess Club" in response.json()
        assert "Programming Class" in response.json()


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_successful(self, client):
        # Arrange
        activity_name = "Test Activity"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_duplicate_registration_prevented(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Already registered for this activity"
        assert len(activities[activity_name]["participants"]) == initial_count
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_multiple_students_same_activity(self, client):
        # Arrange
        activity_name = "Test Activity"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            # Assert each signup succeeds
            assert response.status_code == 200
        
        # Assert
        for email in emails:
            assert email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_student_successful(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_unregister_nonregistered_student_returns_400(self, client):
        # Arrange
        activity_name = "Test Activity"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_allows_student_to_rejoin(self, client):
        # Arrange
        activity_name = "Test Activity"
        email = "student@mergington.edu"
        
        # First, register the student
        client.post(f"/activities/{activity_name}/signup?email={email}")
        # Verify registration was successful
        assert email in activities[activity_name]["participants"]
        assert email in activities[activity_name]["participants"]
        
        # Act: Unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert: Unregister succeeded
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        
        # Act: Re-register
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert: Re-registration succeeded
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestActivityEdgeCases:
    """Tests for edge cases and integration scenarios"""
    
    def test_signup_and_unregister_sequence(self, client):
        # Arrange
        activity_name = "Test Activity"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act & Assert: Sign up first student
        response = client.post(f"/activities/{activity_name}/signup?email={email1}")
        assert response.status_code == 200
        
        # Act & Assert: Sign up second student
        response = client.post(f"/activities/{activity_name}/signup?email={email2}")
        assert response.status_code == 200
        
        # Act & Assert: Unregister first student
        response = client.delete(f"/activities/{activity_name}/unregister?email={email1}")
        assert response.status_code == 200
        assert email1 not in activities[activity_name]["participants"]
        assert email2 in activities[activity_name]["participants"]
    
    def test_participant_count_accuracy(self, client):
        # Arrange
        activity_name = "Test Activity"
        emails = ["s1@test.edu", "s2@test.edu", "s3@test.edu"]
        
        # Act: Sign up all students
        for email in emails:
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act: Get activities
        response = client.get("/activities")
        
        # Assert: Participant count matches
        assert response.status_code == 200
        activity_data = response.json()[activity_name]
        assert len(activity_data["participants"]) == len(emails)
