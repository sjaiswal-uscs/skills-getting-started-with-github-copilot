"""
Test suite for the High School Management System API endpoints.
"""

import pytest
from fastapi import status


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that the root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Test cases for the activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities
        
        # Verify some known activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Soccer Team" in data
        
        # Verify activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestActivitySignup:
    """Test cases for activity signup functionality."""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify the user was actually added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist."""
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that signing up with an already registered email fails."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_new_email_to_existing_activity(self, client, reset_activities):
        """Test signing up a new email to an activity that has existing participants."""
        activity_name = "Programming Class"
        new_email = "newstudent@mergington.edu"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"]
        initial_count = len(initial_participants)
        
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        assert len(updated_participants) == initial_count + 1
        assert new_email in updated_participants


class TestActivityUnregister:
    """Test cases for activity unregistration functionality."""
    
    def test_unregister_from_activity_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Removed {email} from {activity_name}"
        
        # Verify the user was actually removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregistration from an activity that doesn't exist."""
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_email_not_registered(self, client, reset_activities):
        """Test unregistering an email that's not registered for the activity."""
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"
    
    def test_unregister_reduces_participant_count(self, client, reset_activities):
        """Test that unregistering reduces the participant count."""
        activity_name = "Programming Class"
        email = "emma@mergington.edu"  # Already registered
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"]
        initial_count = len(initial_participants)
        
        response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the participant count decreased
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        assert len(updated_participants) == initial_count - 1
        assert email not in updated_participants


class TestActivityDataIntegrity:
    """Test cases for ensuring data integrity across operations."""
    
    def test_signup_and_unregister_cycle(self, client, reset_activities):
        """Test signup followed by unregister restores original state."""
        activity_name = "Art Workshop"
        email = "cyclictest@mergington.edu"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()[activity_name]["participants"].copy()
        
        # Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify signup
        after_signup_response = client.get("/activities")
        after_signup_participants = after_signup_response.json()[activity_name]["participants"]
        assert email in after_signup_participants
        assert len(after_signup_participants) == len(initial_participants) + 1
        
        # Unregister
        unregister_response = client.post(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify back to original state
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity_name]["participants"]
        assert final_participants == initial_participants
    
    def test_multiple_activities_independent(self, client, reset_activities):
        """Test that operations on one activity don't affect others."""
        email = "independence@mergington.edu"
        
        # Get initial state of all activities
        initial_response = client.get("/activities")
        initial_activities = initial_response.json()
        
        # Sign up for one activity
        target_activity = "Soccer Team"
        client.post(f"/activities/{target_activity}/signup?email={email}")
        
        # Verify other activities unchanged
        updated_response = client.get("/activities")
        updated_activities = updated_response.json()
        
        for activity_name, activity_data in initial_activities.items():
            if activity_name != target_activity:
                assert updated_activities[activity_name]["participants"] == activity_data["participants"]
            else:
                assert email in updated_activities[activity_name]["participants"]