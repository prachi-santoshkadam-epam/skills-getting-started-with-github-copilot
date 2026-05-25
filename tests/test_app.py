"""Tests for the Mergington High School Activities API."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestRoot:
    """Tests for the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Club" in activities
    
    def test_get_activities_structure(self, client, reset_activities):
        """Test that activity data has correct structure."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_participants(self, client, reset_activities):
        """Test that participants are returned correctly."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_participants = activities["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant."""
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        chess_participants = activities["Chess Club"]["participants"]
        
        assert "newstudent@mergington.edu" in chess_participants
        assert len(chess_participants) == 3
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup to non-existent activity."""
        response = client.post(
            "/activities/Non-existent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signup for activity when already registered."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test signup for multiple different activities."""
        email = "newstudent@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregister:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        chess_participants = activities["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" not in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 1
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister from non-existent activity."""
        response = client.post(
            "/activities/Non-existent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister when not registered for activity."""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signup followed by unregister."""
        email = "newstudent@mergington.edu"
        
        # Signup
        response1 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Basketball Club"]["participants"]
        
        # Unregister
        response2 = client.post(
            "/activities/Basketball Club/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()["Basketball Club"]["participants"]


class TestIntegration:
    """Integration tests for multiple endpoints."""
    
    def test_full_signup_workflow(self, client, reset_activities):
        """Test complete signup workflow."""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
        assert email not in response.json()[activity]["participants"]
    
    def test_concurrent_signups(self, client, reset_activities):
        """Test multiple students signing up for same activity."""
        activity = "Chess Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Signup multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        
        for email in emails:
            assert email in participants
        
        assert len(participants) == 5  # 2 original + 3 new
