"""
Database Connection Pool Manager
Centralized asyncpg connection pool with health checks and monitoring.
"""
import asyncpg
import os
from typing import Optional
from contextlib import asynccontextmanager
from logger import logger
from env_validator import get_config_int, get_config

class DatabasePool:
    """
    Singleton database connection pool manager.
    Handles connection lifecycle, health checks, and monitoring.
    """
    
    _instance: Optional['DatabasePool'] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def pool(self) -> Optional[asyncpg.Pool]:
        """Get the connection pool"""
        return self._pool
    
    async def initialize(self):
        """
        Initialize the connection pool with environment-based configuration.
        Call this during application startup.
        """
        if self._pool is not None:
            logger.warning("Database pool already initialized")
            return
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Get pool configuration from environment
        min_size = get_config_int("DB_POOL_MIN_SIZE", 5)
        max_size = get_config_int("DB_POOL_MAX_SIZE", 20)
        max_queries = get_config_int("DB_POOL_MAX_QUERIES", 5000)
        
        # Additional pool settings
        command_timeout = get_config_int("DB_COMMAND_TIMEOUT", 60)
        
        logger.info(
            "Initializing database connection pool",
            min_size=min_size,
            max_size=max_size,
            max_queries=max_queries,
        )
        
        try:
            self._pool = await asyncpg.create_pool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                max_queries=max_queries,
                max_inactive_connection_lifetime=300,  # 5 minutes
                command_timeout=command_timeout,
                # Disable statement cache to avoid issues with schema changes
                statement_cache_size=0,
            )
            
            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info(
                "Database pool initialized successfully",
                min_size=min_size,
                max_size=max_size,
            )
            
        except Exception as e:
            logger.error("Failed to initialize database pool", error=str(e))
            raise
    
    async def close(self):
        """
        Close the connection pool gracefully.
        Call this during application shutdown.
        """
        if self._pool is None:
            return
        
        logger.info("Closing database connection pool")
        
        try:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed successfully")
        except Exception as e:
            logger.error("Error closing database pool", error=str(e))
            raise
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool using context manager.
        Ensures connection is always released back to the pool.
        
        Usage:
            async with db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        conn = None
        try:
            conn = await self._pool.acquire()
            yield conn
        except asyncpg.exceptions.TooManyConnectionsError:
            logger.error("Database pool exhausted - too many connections")
            raise
        except asyncpg.exceptions.PoolAcquireTimeoutError:
            logger.error("Timeout acquiring connection from pool")
            raise
        except Exception as e:
            logger.error("Error with database connection", error=str(e))
            raise
        finally:
            if conn is not None:
                try:
                    await self._pool.release(conn)
                except Exception as e:
                    logger.error("Error releasing connection back to pool", error=str(e))
    
    async def execute(self, query: str, *args):
        """
        Execute a query using a pooled connection.
        Convenience method for simple queries.
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """
        Fetch multiple rows using a pooled connection.
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """
        Fetch a single row using a pooled connection.
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """
        Fetch a single value using a pooled connection.
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def get_pool_stats(self) -> dict:
        """
        Get current pool statistics for monitoring.
        
        Returns:
            Dictionary with pool metrics:
            - size: Current number of connections
            - min_size: Minimum pool size
            - max_size: Maximum pool size
            - free: Number of free connections
            - in_use: Number of connections in use
        """
        if self._pool is None:
            return {
                "initialized": False,
                "size": 0,
                "min_size": 0,
                "max_size": 0,
                "free": 0,
                "in_use": 0,
            }
        
        return {
            "initialized": True,
            "size": self._pool.get_size(),
            "min_size": self._pool.get_min_size(),
            "max_size": self._pool.get_max_size(),
            "free": self._pool.get_idle_size(),
            "in_use": self._pool.get_size() - self._pool.get_idle_size(),
        }
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the database connection.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if self._pool is None:
                logger.warning("Health check failed: pool not initialized")
                return False
            
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.debug("Database health check passed")
                    return True
                else:
                    logger.error("Database health check failed: unexpected result")
                    return False
        
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Global singleton instance
db_pool = DatabasePool()


# Convenience functions for backward compatibility
async def get_connection():
    """
    Get a connection from the pool (context manager).
    Use this in `async with` statements.
    """
    return db_pool.acquire()


async def execute_query(query: str, *args):
    """Execute a query"""
    return await db_pool.execute(query, *args)


async def fetch_rows(query: str, *args):
    """Fetch multiple rows"""
    return await db_pool.fetch(query, *args)


async def fetch_one(query: str, *args):
    """Fetch a single row"""
    return await db_pool.fetchrow(query, *args)


async def fetch_value(query: str, *args):
    """Fetch a single value"""
    return await db_pool.fetchval(query, *args)


__all__ = [
    "DatabasePool",
    "db_pool",
    "get_connection",
    "execute_query",
    "fetch_rows",
    "fetch_one",
    "fetch_value",
]

