import argparse


def create_parser():
    parser = argparse.ArgumentParser(description='Run GULL-API using uvicorn.')
    
    # Add arguments similar to what uvicorn accepts
    parser.add_argument('--host', default='0.0.0.0', type=str, help='Bind socket to this host (default: 0.0.0.0)')
    parser.add_argument('--port', default=8000, type=int, help='Bind socket to this port (default: 8000)')
    parser.add_argument('--log-level', default='info', type=str, help='Log level (default: info)')
    parser.add_argument('--workers', default=1, type=int, help='Number of worker processes (default: 1)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    parser.add_argument('--reload-dir', default=None, type=str, help='Set reload directories explicitly, instead of using the current working directory')
    
    return parser


def run_uvicorn(args, uvicorn_module):
    # Call uvicorn.run with the user-specified options
    uvicorn_module.run(
        "gull_api.main:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        workers=args.workers,
        reload=args.reload,
        reload_dirs=[args.reload_dir] if args.reload_dir else None
    )


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # Import uvicorn here so it can be mocked in tests
    import uvicorn
    run_uvicorn(args, uvicorn)


if __name__ == "__main__":  # pragma: no cover
    main()