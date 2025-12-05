"""
Centralized model imports for the Pool Inspection System.

This module provides a single import location for all Django models,
making imports cleaner and more maintainable throughout the codebase.

Instead of:
    from accounts.models import User
    from hotels.models import Hotel
    from pools.models import PoolReading

You can now use:
    from models import User, Hotel, PoolReading

Note: The actual model definitions remain in their respective Django apps
to maintain proper Django app structure and migrations.
"""

from accounts.models import User
from hotels.models import Hotel
from pools.models import PoolReading


__all__ = [
    'User',
    'Hotel',
    'PoolReading',
]
