"""
Tests for AI services (LocalAI and Ollama).

This module contains tests for the AI service diagnostics and functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Import the test utilities
from test_utils import (
    LocalAIDiagnostics,
    OllamaDiagnostics,
    ServiceHealth,
    run_diagnostics
)

class TestAIDiagnostics(unittest.TestCase):
    """Base test class for AI diagnostics."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"status": "ok"}
        self.mock_response.raise_for_status.return_value = None

class TestLocalAIDiagnostics(TestAIDiagnostics):
    """Tests for LocalAIDiagnostics."""
    
    @patch('test_utils.requests.Session')
    def test_check_health_success(self, mock_session):
        """Test successful health check."""
        # Setup mock
        mock_session.return_value.get.return_value = self.mock_response
        
        # Test
        diag = LocalAIDiagnostics("http://localhost:8080")
        health = diag.check_health()
        
        # Assert
        self.assertEqual(health.service_name, "LocalAI")
        self.assertEqual(health.status, "healthy")
        self.assertIsNotNone(health.response_time)
        self.assertIsNotNone(health.details)
    
    @patch('test_utils.requests.Session')
    def test_test_completion(self, mock_session):
        """Test text completion."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"text": "Paris"}]}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response

        # Test
        diag = LocalAIDiagnostics("http://localhost:8080")
        result = diag.test_completion("gpt-4", "What is the capital of France?")

        # Assert
        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["text"], "Paris")

class TestOllamaDiagnostics(TestAIDiagnostics):
    """Tests for OllamaDiagnostics."""
    
    @patch('test_utils.requests.Session')
    def test_check_health_success(self, mock_session):
        """Test successful health check."""
        # Setup mock
        mock_session.return_value.get.return_value = self.mock_response
        
        # Test
        diag = OllamaDiagnostics("http://localhost:11434")
        health = diag.check_health()
        
        # Assert
        self.assertEqual(health.service_name, "Ollama")
        self.assertEqual(health.status, "healthy")
        self.assertIsNotNone(health.response_time)
        self.assertIsNotNone(health.details)
    
    @patch('test_utils.requests.Session')
    def test_test_completion(self, mock_session):
        """Test text completion."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Paris"}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response

        # Test
        diag = OllamaDiagnostics("http://localhost:11434")
        result = diag.test_completion("llama2", "What is the capital of France?")

        # Assert
        self.assertIn("response", result)
        self.assertEqual(result["response"], "Paris")

class TestRunDiagnostics(unittest.TestCase):
    """Tests for the run_diagnostics function."""
    
    @patch('test_utils.LocalAIDiagnostics')
    def test_run_diagnostics_localai(self, mock_diag):
        """Test running diagnostics for LocalAI."""
        # Setup mock
        mock_instance = mock_diag.return_value
        mock_instance.check_health.return_value = ServiceHealth(
            service_name="LocalAI",
            status="healthy",
            response_time=0.1
        )
        mock_instance.test_completion.return_value = {"choices": [{"text": "Paris"}]}
        mock_instance.test_embedding.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        
        # Test
        results = run_diagnostics("http://localhost:8080", "localai")
        
        # Assert
        self.assertEqual(results["health"]["status"], "healthy")
        self.assertEqual(results["completion_test"]["choices"][0]["text"], "Paris")
        self.assertEqual(results["embedding_test"]["embedding_length"], 3)
    
    @patch('test_utils.OllamaDiagnostics')
    def test_run_diagnostics_ollama(self, mock_diag):
        """Test running diagnostics for Ollama."""
        # Setup mock
        mock_instance = mock_diag.return_value
        mock_instance.check_health.return_value = ServiceHealth(
            service_name="Ollama",
            status="healthy",
            response_time=0.1
        )
        mock_instance.test_completion.return_value = {"response": "Paris"}
        mock_instance.test_embedding.return_value = {"embedding": [0.1, 0.2, 0.3]}
        
        # Test
        results = run_diagnostics("http://localhost:11434", "ollama")
        
        # Assert
        self.assertEqual(results["health"]["status"], "healthy")
        self.assertEqual(results["completion_test"]["response"], "Paris")
        self.assertEqual(results["embedding_test"]["embedding_length"], 3)

if __name__ == "__main__":
    unittest.main()
