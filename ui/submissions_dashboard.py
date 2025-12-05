"""Submissions dashboard page component with table, navigation, and search."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

from nicegui import ui

from models import User, PoolReading
from ui.navigation import ROUTE_SUBMISSIONS, ROUTE_FORM_NEW, get_form_view_route


logger = logging.getLogger(__name__)


# Constants
CACHE_TTL_SECONDS = 60  # 1 minute cache
TABLE_ROWS_PER_PAGE = 10
DATE_FORMAT = '%Y-%m-%d %H:%M'


@dataclass
class SubmissionRow:
    """Type-safe representation of a submission row in the dashboard table."""
    id: int
    reference_id: str
    hotel_name: str
    submitted_by: str
    submission_date: str
    status: str
    ph_level: float
    chlorine_ppm: float
    water_clarity: str

    def to_dict(self) -> dict:
        """Convert to dictionary for NiceGUI table."""
        return {
            'id': self.id,
            'reference_id': self.reference_id,
            'hotel_name': self.hotel_name,
            'submitted_by': self.submitted_by,
            'submission_date': self.submission_date,
            'status': self.status,
            'ph_level': self.ph_level,
            'chlorine_ppm': self.chlorine_ppm,
            'water_clarity': self.water_clarity,
        }


class SubmissionsCache:
    """Simple in-memory cache for submissions data."""

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self._data: Optional[list[SubmissionRow]] = None
        self._timestamp: Optional[datetime] = None
        self._user_id: Optional[int] = None
        self._ttl_seconds = ttl_seconds

    def get(self, user_id: int) -> Optional[list[SubmissionRow]]:
        """Get cached data if valid for the given user."""
        if not self._is_valid(user_id):
            return None

        cache_age = (datetime.now() - self._timestamp).total_seconds()
        logger.info(f"✓ Cache HIT - Using cached data (age: {cache_age:.1f}s)")
        return self._data

    def set(self, user_id: int, data: list[SubmissionRow]) -> None:
        """Update cache with new data."""
        self._data = data
        self._timestamp = datetime.now()
        self._user_id = user_id
        logger.info(f"Cache updated for user {user_id}")

    def invalidate(self) -> None:
        """Clear the cache."""
        self._data = None
        self._timestamp = None
        self._user_id = None
        logger.info("Cache invalidated")

    def _is_valid(self, user_id: int) -> bool:
        """Check if cache is valid for the given user."""
        if self._data is None or self._timestamp is None or self._user_id != user_id:
            return False

        age = (datetime.now() - self._timestamp).total_seconds()
        return age < self._ttl_seconds


class SubmissionsDashboardComponent:
    """Component for rendering the submissions dashboard page with navigation, table, and search."""

    def __init__(self, user: User, cache: SubmissionsCache):
        self.user = user
        self.cache = cache
        self.table: Optional[ui.table] = None

    async def load_submissions(self, force_refresh: bool = False) -> list[SubmissionRow]:
        """
        Load pool submissions from database with caching.

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of submission rows
        """
        # Check cache first
        if not force_refresh:
            cached_data = self.cache.get(self.user.id)
            if cached_data is not None:
                return cached_data

        # Cache miss - fetch from database
        logger.info("✗ Cache MISS - Fetching from database")
        submissions = await self._fetch_from_database()

        # Update cache
        self.cache.set(self.user.id, submissions)

        return submissions

    async def _fetch_from_database(self) -> list[SubmissionRow]:
        """Fetch submissions from database based on user permissions."""
        # Build query based on user permissions
        queryset = PoolReading.objects.select_related('submitted_by', 'hotel')

        if not self.user.is_admin:
            queryset = queryset.filter(hotel_id=self.user.hotel_id)

        # Convert to typed rows
        submissions = []
        async for reading in queryset:
            submission = SubmissionRow(
                id=reading.id,
                reference_id=reading.reference_id,
                hotel_name=reading.hotel.name,
                submitted_by=reading.submitted_by.username,
                submission_date=reading.submission_date.strftime(DATE_FORMAT),
                status=reading.get_status_display(),
                ph_level=float(reading.ph_level),
                chlorine_ppm=float(reading.chlorine_ppm),
                water_clarity=reading.get_water_clarity_display()
            )
            submissions.append(submission)

        return submissions

    async def refresh_table(self, force: bool = False) -> None:
        """Refresh the table data."""
        if self.table is None:
            logger.warning("Cannot refresh table - table not initialized")
            return

        submissions = await self.load_submissions(force_refresh=force)
        self.table.rows = [s.to_dict() for s in submissions]
        self.table.update()

    def _handle_row_click(self, event) -> None:
        """Handle table row click event."""
        row_data = event.args[1]
        reference_id = row_data['reference_id']
        ui.navigate.to(get_form_view_route(reference_id))

    def _get_table_columns(self) -> list[dict]:
        """Define table columns configuration."""
        return [
            {
                'name': 'reference_id',
                'label': 'Referans No',
                'field': 'reference_id',
                'align': 'left',
                'sortable': True
            },
            {
                'name': 'hotel_name',
                'label': 'Otel',
                'field': 'hotel_name',
                'align': 'left',
                'sortable': True
            },
            {
                'name': 'submitted_by',
                'label': 'Gönderen',
                'field': 'submitted_by',
                'align': 'left',
                'sortable': True
            },
            {
                'name': 'submission_date',
                'label': 'Tarih',
                'field': 'submission_date',
                'align': 'left',
                'sortable': True
            },
            {
                'name': 'status',
                'label': 'Durum',
                'field': 'status',
                'align': 'left',
                'sortable': True
            },
            {
                'name': 'ph_level',
                'label': 'pH',
                'field': 'ph_level',
                'align': 'left'
            },
            {
                'name': 'chlorine_ppm',
                'label': 'Klor (ppm)',
                'field': 'chlorine_ppm',
                'align': 'left'
            },
            {
                'name': 'water_clarity',
                'label': 'Su Berraklığı',
                'field': 'water_clarity',
                'align': 'left'
            },
        ]

    def _render_navbar(self) -> None:
        """Render the top navigation bar."""
        with ui.header().classes('bg-blue-600 text-white p-4'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Havuz Denetim Sistemi').classes('text-h5 font-bold')
                with ui.row().classes('gap-4'):
                    ui.button('Kontrol Paneli', on_click=lambda: ui.navigate.to(ROUTE_SUBMISSIONS))\
                        .props('flat').classes('text-white')
                    ui.button('Form Doldur', on_click=lambda: ui.navigate.to(ROUTE_FORM_NEW))\
                        .props('flat').classes('text-white')
                    ui.label(f'Kullanıcı: {self.user.username}').classes('text-white ml-4')

    def _render_header(self) -> None:
        """Render the page header section."""
        user_role = 'Yönetici' if self.user.is_admin else 'Kullanıcı'

        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label('Havuz Gönderimleri Kontrol Paneli').classes('text-h3')
            ui.button(
                'Yenile',
                icon='refresh',
                on_click=lambda: self.refresh_table(force=True)
            ).classes('bg-gray-500')

        ui.label(
            f'Giriş yapan: {self.user.username} ({user_role})'
        ).classes('text-subtitle1 mb-6 text-gray-600')

    def _render_table(self) -> None:
        """Render the submissions table."""
        columns = self._get_table_columns()

        self.table = ui.table(
            columns=columns,
            rows=[],
            row_key='id',
            pagination={
                'rowsPerPage': TABLE_ROWS_PER_PAGE,
                'sortBy': 'submission_date',
                'descending': True
            },
        ).classes('w-full')

        self.table.on('rowClick', self._handle_row_click)

        # Add search filter
        with self.table.add_slot('top-left'):
            ui.input(
                'Ara',
                placeholder='Otel, kullanıcı veya duruma göre ara...'
            ).classes('w-64').bind_value(self.table, 'filter')

    async def render(self) -> None:
        """Render the complete submissions table page."""
        self._render_navbar()

        with ui.column().classes('w-full p-8'):
            self._render_header()
            self._render_table()

            # Load initial data
            ui.timer(0.1, lambda: self.refresh_table(), once=True)


# Global cache instance
_cache = SubmissionsCache()


async def render_submissions_dashboard(user: User) -> None:
    """
    Render the submissions dashboard page.

    This is the main entry point used by the router.

    Args:
        user: The authenticated user
    """
    component = SubmissionsDashboardComponent(user, _cache)
    await component.render()
