"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original = {
        key: {"participants": list(value["participants"])}
        for key, value in activities.items()
    }
    yield
    # Restore after test
    for key, value in activities.items():
        value["participants"] = original[key]["participants"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that activities response is a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_keys(self, client):
        """Test that activities have expected keys"""
        response = client.get("/activities")
        activities_data = response.json()
        
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
    
    def test_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_details in activities_data.values():
            assert isinstance(activity_details["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_returns_200(self, client, reset_activities):
        """Test that successfully signing up returns 200"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_returns_success_message(self, client, reset_activities):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds participant to activity"""
        email = "testuser@mergington.edu"
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Test that signing up twice returns 400 error"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Basketball"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_delete_returns_200(self, client, reset_activities):
        """Test that successfully unregistering returns 200"""
        email = "michael@mergington.edu"  # Already signed up
        
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
    
    def test_delete_returns_success_message(self, client, reset_activities):
        """Test that delete returns a success message"""
        email = "michael@mergington.edu"
        
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
    
    def test_delete_removes_participant(self, client, reset_activities):
        """Test that delete actually removes participant from activity"""
        email = "michael@mergington.edu"
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert email not in activities["Chess Club"]["participants"]
    
    def test_delete_nonexistent_student_returns_400(self, client, reset_activities):
        """Test that deleting non-existent participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notexist@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_delete_nonexistent_activity_returns_404(self, client):
        """Test that deleting from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
    
    def test_signup_then_delete(self, client, reset_activities):
        """Test signup followed by delete"""
        email = "flowtest@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        
        # Delete
        delete_response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert delete_response.status_code == 200
        assert email not in activities["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
