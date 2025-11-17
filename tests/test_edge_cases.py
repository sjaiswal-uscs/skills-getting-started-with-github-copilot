"""
Test suite for edge cases and error handling in the High School Management System API.
"""

import pytest
from fastapi import status


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""
    
    def test_activity_names_with_special_characters(self, client, reset_activities):
        """Test handling of activity names with special characters in URLs."""
        # Test with URL encoding for spaces
        response = client.get("/activities")
        activities_data = response.json()
        
        # Test signup with activity name containing spaces
        activity_name = "Chess Club"  # Has space
        email = "spacetest@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == status.HTTP_200_OK
    
    def test_email_parameter_validation(self, client, reset_activities):
        """Test various email formats and parameter handling."""
        activity_name = "Math Olympiad"
        
        # Test with valid email
        valid_email = "valid.email+test@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={valid_email}")
        assert response.status_code == status.HTTP_200_OK
        
        # Test signup without email parameter
        response = client.post(f"/activities/{activity_name}/signup")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_case_sensitivity_activity_names(self, client, reset_activities):
        """Test case sensitivity in activity names."""
        # Test with different case
        response = client.post("/activities/chess club/signup?email=case@test.edu")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response = client.post("/activities/CHESS CLUB/signup?email=case@test.edu")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConcurrentOperations:
    """Test cases simulating concurrent operations."""
    
    def test_multiple_signups_same_activity(self, client, reset_activities):
        """Test multiple users signing up for the same activity."""
        activity_name = "Science Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu", 
            "student3@mergington.edu"
        ]
        
        # Sign up all users
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == status.HTTP_200_OK
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants
    
    def test_signup_unregister_different_users(self, client, reset_activities):
        """Test signup and unregister operations for different users."""
        activity_name = "Drama Club"
        user1 = "user1@mergington.edu"
        user2 = "user2@mergington.edu"
        
        # Both users sign up
        response1 = client.post(f"/activities/{activity_name}/signup?email={user1}")
        response2 = client.post(f"/activities/{activity_name}/signup?email={user2}")
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        # User1 unregisters
        response = client.post(f"/activities/{activity_name}/unregister?email={user1}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify user2 still registered, user1 not
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        assert user1 not in participants
        assert user2 in participants


class TestDataConsistency:
    """Test cases for data consistency and state management."""
    
    def test_activity_structure_preservation(self, client, reset_activities):
        """Test that activity structure is preserved across operations."""
        activity_name = "Basketball Club"
        
        # Get initial structure
        initial_response = client.get("/activities")
        initial_activity = initial_response.json()[activity_name]
        initial_keys = set(initial_activity.keys())
        
        # Perform operations
        client.post(f"/activities/{activity_name}/signup?email=structure@test.edu")
        client.post(f"/activities/{activity_name}/unregister?email=structure@test.edu")
        
        # Verify structure unchanged
        final_response = client.get("/activities")
        final_activity = final_response.json()[activity_name]
        final_keys = set(final_activity.keys())
        
        assert initial_keys == final_keys
        assert final_activity["description"] == initial_activity["description"]
        assert final_activity["schedule"] == initial_activity["schedule"]
        assert final_activity["max_participants"] == initial_activity["max_participants"]
    
    def test_participant_list_type_consistency(self, client, reset_activities):
        """Test that participant lists remain as lists throughout operations."""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list)
            
        # After operations, should still be lists
        client.post("/activities/Gym Class/signup?email=listtest@test.edu")
        
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list)