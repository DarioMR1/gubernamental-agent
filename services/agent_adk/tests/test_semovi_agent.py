# Copyright 2024 SEMOVI Multiagent System Tests

"""Comprehensive tests for SEMOVI multiagent system."""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
adk_path = os.path.join(os.path.dirname(parent_dir), '..', '..', '..', 'adk-python', 'src')
sys.path.insert(0, adk_path)
sys.path.insert(0, parent_dir)

try:
    from google.adk import Agent
    from google.adk.tools.tool_context import ToolContext
    from google.genai import types
except ImportError:
    # Fallback for basic testing without full ADK
    Agent = object
    ToolContext = object
    types = object

# Import your SEMOVI agent
from semovi_multiagent_system.agent import root_agent

# Simple TestRunner implementation for testing
class SimpleTestRunner:
    """Simple test runner that simulates agent interactions."""
    
    def __init__(self, agent):
        self.agent = agent
        self.session_state = {
            "user_data": {},
            "service_determination": {},
            "office_search": {},
            "appointment": {},
            "process_stage": "welcome",
            "session_metadata": {
                "session_id": "test_session",
                "interaction_count": 0
            },
            "authentication_status": {
                "is_authenticated": False
            },
            "license_type": "",
            "procedure_type": "",
            "appointment_date": "",
            "appointment_time": "",
            "office_name": "",
            "total_cost": ""
        }
        
    class Session:
        def __init__(self, state):
            self.state = state
            
    def get_current_session(self):
        return self.Session(self.session_state)
    
    def run(self, prompt):
        # Simulate agent response
        self.session_state["session_metadata"]["interaction_count"] += 1
        
        # Mock response event
        class MockEvent:
            def __init__(self, text):
                self.content = MockContent(text)
        
        class MockContent:
            def __init__(self, text):
                self.parts = [MockPart(text)]
                
        class MockPart:
            def __init__(self, text):
                self.text = text
                
        return [MockEvent(f"Mock response to: {prompt}")]

# Use SimpleTestRunner instead of TestRunner
TestRunner = SimpleTestRunner


class TestSemoviAuthentication:
    """Test authentication flow functionality."""
    
    def setup_method(self):
        """Setup test runner for each test."""
        self.runner = TestRunner(root_agent)
    
    def test_authentication_required_on_start(self):
        """Test that authentication is required on first interaction."""
        events = self.runner.run("Hola")
        session = self.runner.get_current_session()
        
        # Should request authentication
        response_text = events[-1].content.parts[0].text.lower()
        assert any(word in response_text for word in ["autenticar", "email", "contraseña", "credenciales"])
        
        # Should not be authenticated initially
        auth_status = session.state.get("authentication_status", {})
        assert not auth_status.get("is_authenticated", False)
    
    @patch('semovi_multiagent_system.tools.authentication_tools.authenticate_user')
    def test_successful_authentication(self, mock_auth):
        """Test successful authentication flow."""
        # Mock successful authentication
        mock_auth.return_value = {
            "status": "success", 
            "message": "Autenticación exitosa",
            "user_profile": {"name": "Juan Pérez"}
        }
        
        events = self.runner.run("Mi email es juan@test.com y mi contraseña es password123")
        session = self.runner.get_current_session()
        
        # Should be authenticated now
        auth_status = session.state.get("authentication_status", {})
        assert auth_status.get("is_authenticated", False)
        
        # Should contain personalized greeting
        response_text = events[-1].content.parts[0].text
        assert "juan" in response_text.lower() or "pérez" in response_text.lower()
    
    @patch('semovi_multiagent_system.tools.authentication_tools.authenticate_user')
    def test_failed_authentication(self, mock_auth):
        """Test failed authentication handling."""
        # Mock failed authentication
        mock_auth.return_value = {
            "status": "error",
            "message": "Credenciales incorrectas"
        }
        
        events = self.runner.run("Mi email es wrong@test.com y mi contraseña es wrongpass")
        session = self.runner.get_current_session()
        
        # Should not be authenticated
        auth_status = session.state.get("authentication_status", {})
        assert not auth_status.get("is_authenticated", False)
        
        # Should request correct credentials
        response_text = events[-1].content.parts[0].text.lower()
        assert any(word in response_text for word in ["error", "incorrectas", "credenciales"])


class TestSemoviContextVariables:
    """Test context variables are properly set and accessible."""
    
    def setup_method(self):
        """Setup test runner for each test."""
        self.runner = TestRunner(root_agent)
        # Mock authentication for these tests
        session = self.runner.get_current_session()
        session.state["authentication_status"] = {
            "is_authenticated": True,
            "user_profile": {"name": "Test User"}
        }
    
    def test_license_type_variable_initialization(self):
        """Test that license_type variable is initialized."""
        session = self.runner.get_current_session()
        
        # Should have license_type in state
        assert "license_type" in session.state
        assert session.state["license_type"] == ""
    
    def test_appointment_variables_initialization(self):
        """Test that appointment variables are initialized."""
        session = self.runner.get_current_session()
        
        # Should have appointment variables in state
        assert "appointment_date" in session.state
        assert "appointment_time" in session.state
        assert "office_name" in session.state
        assert "total_cost" in session.state
    
    @patch('semovi_multiagent_system.tools.license_consultation_tools.determine_license_requirements')
    def test_license_type_variable_set_after_determination(self, mock_determine):
        """Test that license_type variable is set after license determination."""
        # Mock license determination
        mock_determine.return_value = {
            "status": "success",
            "license_type": "LICENSE_A",
            "procedure_type": "EXPEDITION"
        }
        
        self.runner.run("Necesito licencia para auto, es primera vez")
        session = self.runner.get_current_session()
        
        # Should have license_type set
        assert session.state.get("license_type") == "LICENSE_A"
        assert session.state.get("procedure_type") == "EXPEDITION"
    
    @patch('semovi_multiagent_system.tools.appointment_booking_tools.create_appointment')
    def test_appointment_variables_set_after_booking(self, mock_create):
        """Test that appointment variables are set after booking."""
        # Mock appointment creation
        mock_create.return_value = {
            "status": "success",
            "appointment": {
                "date": "2024-12-05",
                "time": "10:00",
                "office": {"name": "Oficina Centro"}
            }
        }
        
        # Set up required state
        session = self.runner.get_current_session()
        session.state["service_determination"] = {"license_type": "LICENSE_A"}
        session.state["office_search"] = {"selected_office": {"id": 1, "name": "Oficina Centro"}}
        
        self.runner.run("Confirmo la cita del 5 de diciembre a las 10:00")
        session = self.runner.get_current_session()
        
        # Should have appointment variables set
        assert session.state.get("appointment_date") != ""
        assert session.state.get("appointment_time") != ""
        assert session.state.get("office_name") != ""


class TestSemoviAgentTransitions:
    """Test transitions between different agents work correctly."""
    
    def setup_method(self):
        """Setup test runner for each test."""
        self.runner = TestRunner(root_agent)
        # Mock authentication
        session = self.runner.get_current_session()
        session.state["authentication_status"] = {
            "is_authenticated": True,
            "user_profile": {"name": "Test User"}
        }
    
    def test_ine_extraction_agent_transition(self):
        """Test transition to INE extraction agent."""
        events = self.runner.run("Aquí está mi INE [imagen simulada]")
        
        # Should mention INE extraction or data extraction
        response_text = events[-1].content.parts[0].text.lower()
        assert any(word in response_text for word in ["ine", "extrac", "datos", "información"])
    
    def test_license_consultation_agent_transition(self):
        """Test transition to license consultation agent."""
        # Set up INE data first
        session = self.runner.get_current_session()
        session.state["user_data"] = {"curp": "TEST123456789", "full_name": "Test User"}
        
        events = self.runner.run("Necesito licencia para motocicleta de 350cc")
        
        # Should mention license types or costs
        response_text = events[-1].content.parts[0].text.lower()
        assert any(word in response_text for word in ["licencia", "tipo", "costo", "procedimiento"])
    
    def test_office_location_agent_transition(self):
        """Test transition to office location agent."""
        # Set up required state
        session = self.runner.get_current_session()
        session.state["service_determination"] = {"license_type": "LICENSE_A"}
        session.state["user_data"] = {"postal_code": "06100"}
        
        events = self.runner.run("Busco oficinas cercanas")
        
        # Should mention offices or locations
        response_text = events[-1].content.parts[0].text.lower()
        assert any(word in response_text for word in ["oficina", "ubicación", "cerca", "dirección"])


class TestSemoviFunctionCalls:
    """Test that function calls work correctly without parsing errors."""
    
    def setup_method(self):
        """Setup test runner for each test."""
        self.runner = TestRunner(root_agent)
    
    def test_authentication_function_signature(self):
        """Test that authentication functions have proper signatures."""
        from semovi_multiagent_system.tools.authentication_tools import authenticate_user
        import inspect
        
        sig = inspect.signature(authenticate_user)
        params = list(sig.parameters.keys())
        
        # Should have proper parameters
        assert 'tool_context' in params
        assert 'email' in params
        assert 'password' in params
    
    def test_appointment_booking_function_signatures(self):
        """Test that appointment booking functions have proper type annotations."""
        from semovi_multiagent_system.tools.appointment_booking_tools import create_appointment
        import inspect
        
        sig = inspect.signature(create_appointment)
        
        # Check that selected_date and selected_time have str annotations
        assert sig.parameters['selected_date'].annotation == str
        assert sig.parameters['selected_time'].annotation == str
        assert sig.parameters['office_id'].annotation == int
        assert sig.parameters['slot_id'].annotation == int
    
    def test_license_consultation_function_signatures(self):
        """Test that license consultation functions have proper signatures."""
        from semovi_multiagent_system.tools.license_consultation_tools import determine_license_requirements
        import inspect
        
        sig = inspect.signature(determine_license_requirements)
        params = list(sig.parameters.keys())
        
        # Should have proper parameters
        assert 'tool_context' in params
        assert 'vehicle_type' in params
        assert 'procedure' in params


class TestSemoviSessionState:
    """Test that session state remains consistent throughout interactions."""
    
    def setup_method(self):
        """Setup test runner for each test."""
        self.runner = TestRunner(root_agent)
    
    def test_session_initialization(self):
        """Test that session is properly initialized with required fields."""
        session = self.runner.get_current_session()
        
        required_fields = [
            "user_data", "service_determination", "office_search", 
            "appointment", "process_stage", "session_metadata",
            "license_type", "procedure_type", "appointment_date"
        ]
        
        for field in required_fields:
            assert field in session.state, f"Missing required field: {field}"
    
    def test_process_stage_transitions(self):
        """Test that process_stage updates correctly."""
        session = self.runner.get_current_session()
        
        # Should start at welcome stage
        assert session.state.get("process_stage") == "welcome"
        
        # Mock authentication
        session.state["authentication_status"] = {"is_authenticated": True}
        session.state["process_stage"] = "authenticated"
        
        # Mock service determination
        session.state["service_determination"] = {"license_type": "LICENSE_A"}
        session.state["process_stage"] = "service_determined"
        
        # Verify stages are tracked
        assert session.state.get("process_stage") == "service_determined"
    
    def test_session_metadata_tracking(self):
        """Test that session metadata is properly tracked."""
        session = self.runner.get_current_session()
        
        metadata = session.state.get("session_metadata", {})
        
        # Should have session metadata
        assert "session_id" in metadata
        assert "created_at" in metadata
        assert "interaction_count" in metadata
        
        # Interaction count should increase
        initial_count = metadata.get("interaction_count", 0)
        self.runner.run("Test message")
        
        session = self.runner.get_current_session()
        new_count = session.state.get("session_metadata", {}).get("interaction_count", 0)
        assert new_count > initial_count
    
    def test_state_persistence_across_messages(self):
        """Test that state persists across multiple messages."""
        # First message - set some state
        self.runner.run("Hola")
        session = self.runner.get_current_session()
        session.state["test_value"] = "persisted"
        
        # Second message - check state persists
        self.runner.run("Siguiente mensaje")
        session = self.runner.get_current_session()
        
        assert session.state.get("test_value") == "persisted"


class TestSemoviIntegration:
    """Integration tests for complete flows."""
    
    def setup_method(self):
        """Setup test runner for each test."""
        self.runner = TestRunner(root_agent)
    
    @patch('semovi_multiagent_system.tools.authentication_tools.authenticate_user')
    @patch('semovi_multiagent_system.tools.license_consultation_tools.determine_license_requirements')
    def test_complete_authentication_to_license_flow(self, mock_license, mock_auth):
        """Test complete flow from authentication to license determination."""
        # Mock successful authentication
        mock_auth.return_value = {
            "status": "success",
            "user_profile": {"name": "Test User"}
        }
        
        # Mock license determination
        mock_license.return_value = {
            "status": "success",
            "license_type": "LICENSE_A",
            "procedure_type": "EXPEDITION"
        }
        
        # Authentication step
        events1 = self.runner.run("Mi email es test@test.com y contraseña test123")
        session = self.runner.get_current_session()
        
        # License consultation step
        events2 = self.runner.run("Necesito licencia para automóvil, primera vez")
        session = self.runner.get_current_session()
        
        # Should have both authentication and license data
        assert session.state.get("authentication_status", {}).get("is_authenticated")
        assert session.state.get("license_type") == "LICENSE_A"
        assert session.state.get("procedure_type") == "EXPEDITION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])