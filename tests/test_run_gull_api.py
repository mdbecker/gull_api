import pytest
from unittest.mock import Mock, patch, ANY
from gull_api.run_gull_api import create_parser, run_uvicorn, main


def test_run_uvicorn():
    parser = create_parser()
    args = parser.parse_args(['--host', '127.0.0.1', '--port', '8080'])
    
    mock_uvicorn = Mock()
    
    run_uvicorn(args, mock_uvicorn)
    
    mock_uvicorn.run.assert_called_once_with(
        "gull_api.main:app",
        host='127.0.0.1',
        port=8080,
        log_level='info',
        workers=1,
        reload=False,
        reload_dirs=None
    )


def test_main_function():
    with patch('gull_api.run_gull_api.run_uvicorn') as mock_run_uvicorn:
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            mock_args = Mock()
            mock_args.host = '0.0.0.0'
            mock_args.port = 8000
            mock_args.log_level = 'info'
            mock_args.workers = 1
            mock_args.reload = False
            mock_args.reload_dir = None
            mock_parse_args.return_value = mock_args
            
            main()
            
            # Assert that the run_uvicorn function was called with the correct arguments
            mock_run_uvicorn.assert_called_once_with(mock_args, ANY)