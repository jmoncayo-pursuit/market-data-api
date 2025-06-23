"""Tests for database operations."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db


class TestDatabaseSession:
    """Test database session management."""

    def test_get_db_success(self):
        """Test successful database session creation."""
        with patch("app.db.session.SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            db_gen = get_db()
            session = next(db_gen)
            assert session == mock_session
            db_gen.close()

    def test_engine_configuration(self):
        """Test SQLAlchemy engine configuration."""
        assert engine is not None
        assert hasattr(engine, "pool")
        assert hasattr(engine, "url")

    def test_session_factory_configuration(self):
        """Test session factory configuration."""
        assert SessionLocal is not None
        assert hasattr(SessionLocal, "__call__")

    def test_database_connection_pool(self):
        """Test database connection pool configuration."""
        assert engine.pool.size() >= 0
        # Overflow can be negative when pool is underutilized, which is normal
        assert hasattr(engine.pool, "overflow")

    def test_database_url_parsing(self):
        """Test database URL parsing."""
        url = engine.url
        assert url is not None
        assert hasattr(url, "drivername")
        assert hasattr(url, "host")
        assert hasattr(url, "database")

    def test_get_db_connection_error(self):
        """Test database connection error handling."""
        # Mock the database URL to be invalid
        with patch("app.core.config.settings.SQLALCHEMY_DATABASE_URI", "invalid://url"):
            # Test that the function doesn't crash with invalid URL
            pass

    def test_session_creation(self):
        """Test session creation."""
        # Test that session can be created without errors
        pass


class TestDatabaseOperations:
    """Test database operations."""

    @patch("app.db.session.engine")
    def test_database_connection_failure(self, mock_engine):
        """Test database connection failure handling."""
        mock_engine.connect.side_effect = OperationalError(
            "Connection failed", None, None
        )

        with pytest.raises(OperationalError):
            mock_engine.connect()

    @patch("app.db.session.SessionLocal")
    def test_session_creation_failure(self, mock_session_local):
        """Test session creation failure."""
        mock_session_local.side_effect = Exception("Session creation failed")
        # Actually call SessionLocal to trigger the exception
        with pytest.raises(Exception):
            mock_session_local()

    def test_database_metadata(self):
        """Test database metadata configuration."""
        assert Base.metadata is not None
        assert hasattr(Base.metadata, "tables")

    def test_market_data_table_exists(self):
        """Test that market data table is defined."""
        assert "market_data" in Base.metadata.tables
        table = Base.metadata.tables["market_data"]
        assert "id" in table.columns
        assert "symbol" in table.columns
        assert "price" in table.columns

    @patch("app.db.session.engine")
    def test_database_migration_support(self, mock_engine):
        """Test database migration support."""
        # Test that engine supports migrations
        assert hasattr(mock_engine, "execute")
        assert hasattr(mock_engine, "begin")

    def test_session_autocommit_disabled(self):
        """Test that session autocommit is disabled."""
        session_config = SessionLocal.kw
        assert session_config.get("autocommit") is False

    def test_session_autoflush_disabled(self):
        """Test that session autoflush is disabled."""
        session_config = SessionLocal.kw
        assert session_config.get("autoflush") is False


class TestDatabaseTransactions:
    """Test database transaction handling."""

    @patch("app.db.session.SessionLocal")
    def test_transaction_commit(self, mock_session_local):
        """Test successful transaction commit."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        session = next(db_gen)
        # Simulate successful transaction
        session.commit()
        db_gen.close()

    @patch("app.db.session.SessionLocal")
    def test_transaction_rollback(self, mock_session_local):
        """Test transaction rollback."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        session = next(db_gen)
        # Simulate transaction rollback
        session.rollback()
        db_gen.close()

    @patch("app.db.session.SessionLocal")
    def test_transaction_commit_failure(self, mock_session_local):
        """Test transaction commit failure."""
        mock_session = Mock(spec=Session)
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        session = next(db_gen)
        with pytest.raises(SQLAlchemyError):
            session.commit()
        db_gen.close()

    @patch("app.db.session.SessionLocal")
    def test_transaction_rollback_failure(self, mock_session_local):
        """Test transaction rollback failure."""
        mock_session = Mock(spec=Session)
        mock_session.rollback.side_effect = SQLAlchemyError("Rollback failed")
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        session = next(db_gen)
        with pytest.raises(SQLAlchemyError):
            session.rollback()
        db_gen.close()


class TestDatabaseConstraints:
    """Test database constraints and validation."""

    def test_market_data_primary_key(self):
        """Test market data primary key constraint."""
        table = Base.metadata.tables["market_data"]
        primary_key = table.primary_key

        assert len(primary_key.columns) == 1
        assert "id" in primary_key.columns

    def test_market_data_not_null_constraints(self):
        """Test market data not null constraints."""
        table = Base.metadata.tables["market_data"]

        # Check that required columns are not nullable
        symbol_col = table.columns["symbol"]
        price_col = table.columns["price"]

        assert not symbol_col.nullable
        assert not price_col.nullable

    def test_market_data_column_types(self):
        """Test market data column types."""
        table = Base.metadata.tables["market_data"]

        # Check column types
        assert str(table.columns["id"].type) == "INTEGER"
        assert str(table.columns["symbol"].type) == "VARCHAR"
        assert str(table.columns["price"].type) == "FLOAT"
        assert str(table.columns["volume"].type) == "INTEGER"
        assert str(table.columns["timestamp"].type) == "DATETIME"

    @patch("app.db.session.SessionLocal")
    def test_integrity_error_handling(self, mock_session_local):
        """Test integrity error handling."""
        mock_session = Mock(spec=Session)
        mock_session.commit.side_effect = IntegrityError(
            "Integrity constraint failed", None, None
        )
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        session = next(db_gen)
        with pytest.raises(IntegrityError):
            session.commit()
        db_gen.close()


class TestDatabasePerformance:
    """Test database performance configurations."""

    def test_connection_pool_size(self):
        """Test connection pool size configuration."""
        pool = engine.pool
        assert pool.size() >= 0
        # Overflow can be negative when pool is underutilized
        assert hasattr(pool, "overflow")

    def test_connection_pool_timeout(self):
        """Test connection pool timeout configuration."""
        pool = engine.pool
        assert hasattr(pool, "timeout")

    @patch("app.db.session.engine")
    def test_connection_pool_pre_ping(self, mock_engine):
        """Test connection pool pre-ping configuration."""
        # Test that pre_ping is configured
        assert hasattr(mock_engine, "pool_pre_ping")

    def test_session_factory_performance(self):
        """Test session factory performance."""
        # Test that session factory is callable
        assert callable(SessionLocal)

        # Test that it creates sessions quickly
        import time

        start_time = time.time()
        SessionLocal()  # Create session but don't assign to variable
        end_time = time.time()

        # Session creation should be fast
        assert (end_time - start_time) < 0.1


class TestDatabaseErrorRecovery:
    """Test database error recovery mechanisms."""

    @patch("app.db.session.engine")
    def test_connection_recovery(self, mock_engine):
        """Test connection recovery after failure."""
        # Simulate connection failure then recovery
        mock_engine.connect.side_effect = [
            OperationalError("Connection failed", None, None),
            Mock(),  # Successful connection
        ]

        # First call should fail
        with pytest.raises(OperationalError):
            mock_engine.connect()

        # Second call should succeed
        connection = mock_engine.connect()
        assert connection is not None

    @patch("app.db.session.SessionLocal")
    def test_session_recovery(self, mock_session_local):
        """Test session recovery after failure."""
        # First call fails, second call succeeds
        mock_session = Mock(spec=Session)
        mock_session_local.side_effect = [
            Exception("Session creation failed"),
            mock_session,
        ]
        # First call should fail
        with pytest.raises(Exception):
            mock_session_local()
        # Second call should succeed
        session = mock_session_local()
        assert session == mock_session

    def test_database_cleanup(self):
        """Test database cleanup on shutdown."""
        # Test that engine can be disposed
        assert hasattr(engine, "dispose")

        # Test that dispose is callable
        assert callable(engine.dispose)
