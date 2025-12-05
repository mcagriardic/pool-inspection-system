"""Application configuration for deployment settings."""

import os

# Path prefix for deployment
PATH_PREFIX = os.getenv('PATH_PREFIX', '')

# Remove trailing slash if present
PATH_PREFIX = PATH_PREFIX.rstrip('/')

def get_route(path: str) -> str:
    """
    Get the full route path with prefix.

    Args:
        path: The route path (should start with /)

    Returns:
        The full route with prefix
    """
    if not path.startswith('/'):
        path = f'/{path}'

    if PATH_PREFIX:
        return f'{PATH_PREFIX}{path}'
    return path


def get_navigation_path(path: str) -> str:
    """
    Get the navigation path for ui.navigate.to().

    Args:
        path: The target path (should start with /)

    Returns:
        The full path with prefix
    """
    return get_route(path)
