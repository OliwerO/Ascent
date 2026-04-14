"""Shared test fixtures for Ascent tests."""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace


class MockSupabaseResult:
    """Mimics supabase query result with .data attribute."""
    def __init__(self, data):
        self.data = data


class MockSupabaseTable:
    """Chainable mock for supabase.table('x').select(...).eq(...).execute()."""
    def __init__(self, data=None, client=None, table_name=None):
        self._data = data or []
        self._client = client
        self._table_name = table_name

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def in_(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def upsert(self, *args, **kwargs):
        return self

    def update(self, data, **kwargs):
        """Track update calls for verification."""
        if self._client is not None:
            self._client._updates.append((self._table_name, data))
        return self

    def delete(self):
        return self

    def execute(self):
        return MockSupabaseResult(self._data)


class MockSupabaseClient:
    """Mock Supabase client for unit tests."""
    def __init__(self):
        self._tables = {}
        self._updates = []  # List of (table_name, data) for verification

    def set_table_data(self, table_name: str, data: list):
        self._tables[table_name] = data

    def table(self, name: str):
        return MockSupabaseTable(self._tables.get(name, []), client=self, table_name=name)


@pytest.fixture
def mock_sb():
    """Provide a mock Supabase client."""
    return MockSupabaseClient()


@pytest.fixture
def sample_training_sets():
    """Sample training_sets data for progression tests."""
    return [
        {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 1, "session_id": 1, "date": "2026-04-01"},
        {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 2, "session_id": 1, "date": "2026-04-01"},
        {"weight_kg": 70.0, "reps": 8, "rpe": 7, "set_number": 3, "session_id": 1, "date": "2026-04-01"},
    ]


@pytest.fixture
def sample_interference_data():
    """Sample mountain_gym_interference view rows."""
    return [
        {
            "gym_date": "2026-03-20",
            "mountain_load_category": "none",
            "mountain_elevation_72h": 0,
            "mountain_duration_72h_hours": 0,
            "mountain_days_72h": 0,
            "total_volume_kg": 5000,
            "srpe": 6,
            "resort_days_72h": 0,
        },
        {
            "gym_date": "2026-03-22",
            "mountain_load_category": "heavy",
            "mountain_elevation_72h": 2000,
            "mountain_duration_72h_hours": 6,
            "mountain_days_72h": 1,
            "total_volume_kg": 4000,
            "srpe": 8,
            "resort_days_72h": 0,
        },
        {
            "gym_date": "2026-03-25",
            "mountain_load_category": "moderate",
            "mountain_elevation_72h": 1200,
            "mountain_duration_72h_hours": 3.5,
            "mountain_days_72h": 1,
            "total_volume_kg": 4500,
            "srpe": 7,
            "resort_days_72h": 0,
        },
        {
            "gym_date": "2026-03-27",
            "mountain_load_category": "none",
            "mountain_elevation_72h": 0,
            "mountain_duration_72h_hours": 0,
            "mountain_days_72h": 0,
            "total_volume_kg": 5200,
            "srpe": 6,
            "resort_days_72h": 0,
        },
    ]
