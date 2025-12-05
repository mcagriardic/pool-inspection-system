"""Navigation helper module for path management."""

from config.app_config import get_navigation_path

# Define all routes
ROUTE_LOGIN = get_navigation_path('/')
ROUTE_SUBMISSIONS = get_navigation_path('/submissions')
ROUTE_FORM_NEW = get_navigation_path('/form')

def get_form_view_route(ref_id: str) -> str:
    """Get the route for viewing/editing a form by reference ID."""
    return get_navigation_path(f'/form/{ref_id}')
