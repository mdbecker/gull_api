from importlib.metadata import version, PackageNotFoundError

try:
    # Change 'gull-api' to the name of your package as it appears in pyproject.toml
    __version__ = version('gull-api')
except PackageNotFoundError:
    # Package is not installed
    __version__ = None