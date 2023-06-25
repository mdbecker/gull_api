import pytest
from unittest.mock import patch, MagicMock, mock_open
from sqlalchemy.orm import Session, sessionmaker
import gull_api.db as db
from sqlalchemy.exc import SQLAlchemyError


@patch('gull_api.db.create_engine')
@patch('gull_api.db.load_db_config')
def test_get_engine_initialization(mock_load_db_config, mock_create_engine):
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    
    # mocking the load_db_config function to return a dummy db_uri
    mock_load_db_config.return_value = {"db_uri": "mock_db_uri"}
    
    # Calling the get_engine function, which should call create_engine with the correct db_uri
    returned_engine = db.get_engine()
    
    # Check if the create_engine was called with the correct db_uri
    mock_create_engine.assert_called_once_with("mock_db_uri")
    
    # Check if the correct engine is returned
    assert returned_engine == mock_engine

@patch('gull_api.db.SessionManager.__exit__')
@patch('gull_api.db.SessionManager.__enter__')
def test_session_manager(mock_enter, mock_exit):
    mock_session = MagicMock(spec=Session)
    mock_log = MagicMock(spec=db.APIRequestLog)

    session_manager = db.SessionManager(mock_log, session_maker=lambda: mock_session)

    with session_manager as session:
        mock_session.add.assert_called_once_with(mock_log)
        assert session == mock_session

    mock_exit.assert_called_once()

def test_session_manager_with_error():
    mock_session = MagicMock(spec=Session)
    mock_log = MagicMock(spec=db.APIRequestLog)
    mock_session.commit.side_effect = SQLAlchemyError  # set side_effect to the exception class
    
    session_manager = db.SessionManager(mock_log, session_maker=lambda: mock_session)

    # This should raise SQLAlchemyError and thus, a rollback should happen.
    with pytest.raises(SQLAlchemyError):
        with session_manager as session:
            raise SQLAlchemyError()  # raise actual exception

    mock_session.rollback.assert_called_once()

@patch("builtins.open", new_callable=mock_open, read_data='{"db_uri": "test_db_uri"}')
def test_load_db_config_file_exists(mock_open):
    result = db.load_db_config()
    assert result == {"db_uri": "test_db_uri"}

@patch("builtins.open", side_effect=FileNotFoundError())
def test_load_db_config_file_not_found(mock_open):
    result = db.load_db_config()
    assert result == {"db_uri": "sqlite:////app/data/database.db"}

@patch('gull_api.db.sqlalchemy.exc.SQLAlchemyError', new_callable=MagicMock)
def test_session_manager_with_context_error(mock_exception):
    mock_session = MagicMock(spec=Session)
    mock_log = MagicMock(spec=db.APIRequestLog)
    mock_session.commit.side_effect = None  # No error during commit

    session_manager = db.SessionManager(mock_log, session_maker=lambda: mock_session)

    with pytest.raises(Exception):
        with session_manager as session:
            raise Exception("An error occurred")

    mock_session.commit.assert_called_once()  # Session should still be committed

@patch('gull_api.db.sqlalchemy.exc.SQLAlchemyError', new_callable=MagicMock)
def test_session_close_on_exit(mock_exception):
    mock_session = MagicMock(spec=Session)
    mock_log = MagicMock(spec=db.APIRequestLog)
    mock_session.commit.side_effect = None

    session_manager = db.SessionManager(mock_log, session_maker=lambda: mock_session)

    with session_manager as session:
        pass  # No operation, just exit the context

    mock_session.close.assert_called_once()  # Session should be closed on exit

@patch('gull_api.db.create_engine')
@patch('gull_api.db.load_db_config')
@patch.object(db.Base.metadata, 'create_all')
def test_get_session_maker_without_engine(mock_create_all, mock_load_db_config, mock_create_engine):
    # Mock the engine
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    # Mock the db_config
    mock_load_db_config.return_value = {"db_uri": "mock_db_uri"}

    # Calling the get_session_maker function without providing an engine
    returned_session_maker = db.get_session_maker()

    # Check if get_engine was called
    mock_create_engine.assert_called_once_with("mock_db_uri")

    # Check if session_maker has been called with the correct engine
    assert isinstance(returned_session_maker, sessionmaker)
    assert returned_session_maker.kw['bind'] == mock_engine

    # Check if metadata.create_all was called with the correct engine
    mock_create_all.assert_called_once_with(bind=mock_engine)