"""
Tests for environment variable validation
"""
import pytest
import os
from env_validator import validate_env, EnvValidationError


def test_env_validation_missing_database_url(monkeypatch):
    """Test that validation fails when DATABASE_URL is missing"""
    # Remove DATABASE_URL
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SESSION_SECRET", "a" * 32)
    monkeypatch.setenv("NODE_ENV", "development")
    
    with pytest.raises(EnvValidationError):
        validate_env()


def test_env_validation_missing_anthropic_key(monkeypatch):
    """Test that validation fails when ANTHROPIC_API_KEY is missing"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "a" * 32)
    monkeypatch.setenv("NODE_ENV", "development")
    
    with pytest.raises(EnvValidationError):
        validate_env()


def test_env_validation_short_session_secret(monkeypatch):
    """Test that validation fails when SESSION_SECRET is too short"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SESSION_SECRET", "short")  # Less than 32 chars
    monkeypatch.setenv("NODE_ENV", "development")
    
    with pytest.raises(EnvValidationError):
        validate_env()


def test_env_validation_invalid_node_env(monkeypatch):
    """Test that validation warns for invalid NODE_ENV"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SESSION_SECRET", "a" * 32)
    monkeypatch.setenv("NODE_ENV", "invalid")
    
    with pytest.raises(EnvValidationError):
        validate_env()


def test_env_validation_success(monkeypatch):
    """Test that validation passes with all required variables"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-test")
    monkeypatch.setenv("SESSION_SECRET", "a" * 32)
    monkeypatch.setenv("NODE_ENV", "development")
    
    # Should not raise
    validate_env()

