"""
Environment Variables Validator
Validates that all required environment variables are set before starting the application.
"""
import os
import sys
from typing import List, Tuple, Optional

class EnvValidationError(Exception):
    """Raised when required environment variables are missing or invalid"""
    pass

# Required environment variables (system won't start without these)
REQUIRED_VARS = [
    ("DATABASE_URL", "PostgreSQL connection string"),
    ("ANTHROPIC_API_KEY", "Anthropic Claude API key"),
    ("SESSION_SECRET", "Session encryption secret (min 32 chars)"),
    ("NODE_ENV", "Environment: development, production, or test"),
]

# Optional variables with fallback values
OPTIONAL_VARS = [
    ("PERPLEXITY_API_KEY", "Perplexity API for research", None),
    ("YOUTUBE_API_KEY", "YouTube Data API v3", None),
    ("UNSPLASH_ACCESS_KEY", "Unsplash API for avatars", None),
    ("REDIS_URL", "Redis connection string", None),
    ("SENTRY_DSN", "Sentry error tracking DSN", None),
]

# Configuration variables with defaults
CONFIG_VARS = [
    ("DB_POOL_MIN_SIZE", "5"),
    ("DB_POOL_MAX_SIZE", "20"),
    ("DB_POOL_MAX_QUERIES", "5000"),
    ("ANTHROPIC_TIMEOUT", "60"),
    ("ANTHROPIC_MAX_RETRIES", "3"),
    ("ANTHROPIC_RETRY_DELAY", "1"),
    ("CIRCUIT_BREAKER_THRESHOLD", "5"),
    ("CIRCUIT_BREAKER_TIMEOUT", "300"),
    ("LOG_LEVEL", "INFO"),
    ("LOG_FORMAT", "json"),
    ("RATE_LIMIT_COUNCIL_PER_HOUR", "10"),
    ("RATE_LIMIT_ENRICHMENT_PER_DAY", "3"),
    ("RATE_LIMIT_AUTO_CLONE_PER_DAY", "5"),
    ("RATE_LIMIT_UPLOAD_PER_HOUR", "10"),
    ("MAX_UPLOAD_SIZE_MB", "5"),
    ("MAX_IMAGE_DIMENSION", "2048"),
    ("SESSION_MAX_AGE_HOURS", "1"),
    ("CSRF_ENABLED", "true"),
    ("BACKUP_ENABLED", "true"),
    ("BACKUP_RETENTION_DAYS", "30"),
    ("HEALTH_CHECK_ENABLED", "true"),
    ("PYTHON_BACKEND_PORT", "5002"),
    ("NODE_SERVER_PORT", "3001"),
]


def validate_required_vars() -> Tuple[bool, List[str]]:
    """
    Validate that all required environment variables are set.
    
    Returns:
        Tuple of (is_valid, missing_vars)
    """
    missing = []
    
    for var_name, description in REQUIRED_VARS:
        value = os.getenv(var_name)
        if not value:
            missing.append(f"  ❌ {var_name}: {description}")
        else:
            # Additional validations
            if var_name == "SESSION_SECRET" and len(value) < 32:
                missing.append(f"  ⚠️  {var_name}: Must be at least 32 characters (currently {len(value)})")
            elif var_name == "NODE_ENV" and value not in ["development", "production", "test"]:
                missing.append(f"  ⚠️  {var_name}: Must be 'development', 'production', or 'test' (currently '{value}')")
    
    return len(missing) == 0, missing


def check_optional_vars() -> List[str]:
    """Check which optional variables are missing (informational only)"""
    missing = []
    
    for var_name, description, _ in OPTIONAL_VARS:
        if not os.getenv(var_name):
            missing.append(f"  ℹ️  {var_name}: {description} (optional, will be skipped)")
    
    return missing


def set_default_config_vars():
    """Set default values for configuration variables if not provided"""
    for var_name, default_value in CONFIG_VARS:
        if not os.getenv(var_name):
            os.environ[var_name] = default_value


def validate_env() -> None:
    """
    Main validation function. Call this on application startup.
    Raises EnvValidationError if validation fails.
    """
    print("\n" + "="*70)
    print("🔍 VALIDANDO VARIÁVEIS DE AMBIENTE...")
    print("="*70 + "\n")
    
    # Validate required variables
    is_valid, missing_required = validate_required_vars()
    
    if not is_valid:
        error_msg = (
            "\n" + "="*70 + "\n"
            "❌ ERRO: Variáveis de ambiente obrigatórias não encontradas!\n"
            "="*70 + "\n\n"
            "Variáveis faltando:\n" +
            "\n".join(missing_required) + "\n\n"
            "📖 Como corrigir:\n"
            "  1. Crie um arquivo .env na raiz do projeto\n"
            "  2. Adicione as variáveis listadas acima\n"
            "  3. Veja ENV_VARIABLES.md para detalhes\n\n"
            "Exemplo mínimo .env:\n"
            "  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/advisory\n"
            "  ANTHROPIC_API_KEY=sk-ant-api03-your-key-here\n"
            "  SESSION_SECRET=$(openssl rand -base64 32)\n"
            "  NODE_ENV=development\n"
            "\n" + "="*70 + "\n"
        )
        raise EnvValidationError(error_msg)
    
    print("✅ Variáveis obrigatórias: OK\n")
    
    # Check optional variables (informational)
    missing_optional = check_optional_vars()
    if missing_optional:
        print("ℹ️  Variáveis opcionais ausentes (funcionalidades limitadas):")
        for msg in missing_optional:
            print(msg)
        print()
    
    # Set default configuration values
    set_default_config_vars()
    print("⚙️  Configurações: Valores padrão aplicados\n")
    
    # Print summary
    env = os.getenv("NODE_ENV", "unknown")
    db_url = os.getenv("DATABASE_URL", "")
    db_host = db_url.split("@")[1].split("/")[0] if "@" in db_url else "unknown"
    
    print("="*70)
    print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print(f"  🌍 Ambiente: {env}")
    print(f"  🗄️  Database: {db_host}")
    print(f"  🤖 Anthropic API: Configurada")
    print(f"  🔐 Session Secret: {'✓' if len(os.getenv('SESSION_SECRET', '')) >= 32 else '⚠️'}")
    print("="*70 + "\n")


def get_config(var_name: str, default: Optional[str] = None) -> str:
    """
    Get a configuration value from environment.
    Returns default if not set.
    """
    return os.getenv(var_name, default or "")


def get_config_int(var_name: str, default: int) -> int:
    """Get an integer configuration value"""
    try:
        return int(os.getenv(var_name, str(default)))
    except ValueError:
        return default


def get_config_bool(var_name: str, default: bool) -> bool:
    """Get a boolean configuration value"""
    value = os.getenv(var_name, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_config_float(var_name: str, default: float) -> float:
    """Get a float configuration value"""
    try:
        return float(os.getenv(var_name, str(default)))
    except ValueError:
        return default


if __name__ == "__main__":
    """Run validation as a standalone script"""
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Load .env file
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)
        
        # Run validation
        validate_env()
        
        print("✅ Todas as validações passaram!\n")
        sys.exit(0)
        
    except EnvValidationError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}\n", file=sys.stderr)
        sys.exit(1)

