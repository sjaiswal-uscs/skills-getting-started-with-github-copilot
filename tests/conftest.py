"""
Test configuration and fixtures for the FastAPI application tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to the original state after each test."""
    # Store original state
    original_activities = {
        activity_name: {
            "description": activity["description"],
            "schedule": activity["schedule"], 
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for activity_name, activity in activities.items()
    }
    
    yield
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)