# Copyright 2024 SEMOVI Multiagent System Tests

"""Test configuration and fixtures for SEMOVI tests."""

import os
import sys
import warnings
from dotenv import load_dotenv
import pytest
from unittest.mock import patch, MagicMock

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def load_env_for_semovi_tests():
    """Load environment variables for SEMOVI tests."""
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True, verbose=True)
    
    # Set default test environment variables
    os.environ.setdefault('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE')
    os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
    os.environ.setdefault('SUPABASE_KEY', 'test_key')
    
    # Warn about missing keys
    if 'GOOGLE_API_KEY' not in os.environ:
        warnings.warn('Missing GOOGLE_API_KEY - tests may fail')

load_env_for_semovi_tests()


@pytest.fixture(autouse=True)
def mock_supabase_calls():
    """Mock all Supabase calls to avoid external dependencies."""
    with patch('semovi_multiagent_system.tools.supabase_connection.execute_supabase_query') as mock_query:
        # Mock successful responses for different queries
        def mock_supabase_response(*args, **kwargs):
            endpoint = kwargs.get('endpoint', '')
            
            if 'authenticate' in endpoint:
                return {
                    'status': 'success',
                    'data': [{'id': 'test_user', 'name': 'Test User', 'email': 'test@test.com'}]
                }
            elif 'time_slots' in endpoint:
                return {
                    'status': 'success', 
                    'data': [
                        {'id': 1, 'date': '2024-12-10', 'time': '10:00', 'available_capacity': 5},
                        {'id': 2, 'date': '2024-12-10', 'time': '14:00', 'available_capacity': 3}
                    ]
                }
            elif 'offices' in endpoint:
                return {
                    'status': 'success',
                    'data': [
                        {'id': 1, 'name': 'Oficina Centro', 'address': 'Centro CDMX', 'postal_code': '06100'}
                    ]
                }
            elif 'appointments' in endpoint:
                return {
                    'status': 'success',
                    'data': [{'id': 'apt_123', 'created_at': '2024-12-01T10:00:00Z'}]
                }
            else:
                return {'status': 'success', 'data': []}
                
        mock_query.side_effect = mock_supabase_response
        yield mock_query


@pytest.fixture
def mock_authentication():
    """Mock authentication tools for testing."""
    with patch('semovi_multiagent_system.tools.authentication_tools.authenticate_user') as mock_auth:
        mock_auth.return_value = {
            'status': 'success',
            'message': 'Autenticación exitosa',
            'user_profile': {'name': 'Test User', 'email': 'test@test.com'}
        }
        yield mock_auth


@pytest.fixture
def mock_license_determination():
    """Mock license determination for testing."""
    with patch('semovi_multiagent_system.tools.license_consultation_tools.determine_license_requirements') as mock_license:
        mock_license.return_value = {
            'status': 'success',
            'license_type': 'LICENSE_A',
            'procedure_type': 'EXPEDITION',
            'costs': {'total_cost': 866.0},
            'requirements': {'total_requirements': 5}
        }
        yield mock_license


@pytest.fixture
def mock_ine_extraction():
    """Mock INE extraction for testing."""
    with patch('semovi_multiagent_system.tools.ine_extraction_tools.extract_ine_data_with_vision') as mock_ine:
        mock_ine.return_value = {
            'status': 'success',
            'extracted_data': {
                'full_name': 'Juan Pérez García',
                'curp': 'PEGJ850101HDFRXN01',
                'address': 'Calle Principal 123',
                'postal_code': '06100',
                'birth_date': '1985-01-01'
            }
        }
        yield mock_ine


@pytest.fixture
def authenticated_session():
    """Fixture that provides a session with authentication already completed."""
    from test_semovi_agent import TestRunner
    from semovi_multiagent_system.agent import root_agent
    
    runner = TestRunner(root_agent)
    session = runner.get_current_session()
    
    # Set authenticated state
    session.state["authentication_status"] = {
        "is_authenticated": True,
        "user_profile": {"name": "Test User", "email": "test@test.com"},
        "auth_user_id": "test_user_123"
    }
    session.state["process_stage"] = "authenticated"
    
    return runner


@pytest.fixture
def session_with_user_data():
    """Fixture that provides a session with user data extracted."""
    from test_semovi_agent import TestRunner
    from semovi_multiagent_system.agent import root_agent
    
    runner = TestRunner(root_agent)
    session = runner.get_current_session()
    
    # Set authenticated state and user data
    session.state["authentication_status"] = {
        "is_authenticated": True,
        "user_profile": {"name": "Juan Pérez", "email": "juan@test.com"}
    }
    session.state["user_data"] = {
        "full_name": "Juan Pérez García",
        "curp": "PEGJ850101HDFRXN01", 
        "address": "Calle Principal 123",
        "postal_code": "06100",
        "birth_date": "1985-01-01"
    }
    session.state["process_stage"] = "ine_extracted"
    
    return runner


@pytest.fixture
def session_with_service_determination():
    """Fixture that provides a session with service already determined."""
    from test_semovi_agent import TestRunner
    from semovi_multiagent_system.agent import root_agent
    
    runner = TestRunner(root_agent)
    session = runner.get_current_session()
    
    # Set full state up to service determination
    session.state["authentication_status"] = {"is_authenticated": True}
    session.state["user_data"] = {
        "full_name": "Juan Pérez García",
        "curp": "PEGJ850101HDFRXN01"
    }
    session.state["service_determination"] = {
        "license_type": "LICENSE_A",
        "procedure_type": "EXPEDITION", 
        "costs": {"total_cost": 866.0}
    }
    session.state["license_type"] = "LICENSE_A"
    session.state["procedure_type"] = "EXPEDITION"
    session.state["process_stage"] = "service_determined"
    
    return runner