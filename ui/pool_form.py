"""Pool reading form UI component for creating and editing pool inspections."""

from dataclasses import dataclass
from typing import Optional
import logging

from asgiref.sync import sync_to_async
from nicegui import ui

from models import User, PoolReading
from services.pool_reading_service import (
    submit_pool_reading,
    PoolReadingSubmissionResult
)
from ui.navigation import ROUTE_SUBMISSIONS, ROUTE_FORM_NEW


logger = logging.getLogger(__name__)


# Constants
DEFAULT_PH_LEVEL = 7.2
DEFAULT_CHLORINE_PPM = 1.0
DEFAULT_ALKALINITY_PPM = 100
DEFAULT_TEMPERATURE_CELSIUS = 26.0
DEFAULT_WATER_CLARITY = 'clear'

PH_MIN = 0.0
PH_MAX = 14.0
PH_STEP = 0.1

CHLORINE_MIN = 0.0
CHLORINE_STEP = 0.1

ALKALINITY_MIN = 0
ALKALINITY_STEP = 1

TEMPERATURE_MIN = 0.0
TEMPERATURE_STEP = 0.1

# Statuses that lock the form from editing
READONLY_STATUSES = {'in_progress', 'completed'}


@dataclass
class FormState:
    """Type-safe form state for pool reading data."""
    hotel: str = ''
    status: str = 'open'
    ph_level: float = DEFAULT_PH_LEVEL
    chlorine_ppm: float = DEFAULT_CHLORINE_PPM
    alkalinity_ppm: int = DEFAULT_ALKALINITY_PPM
    temperature_celsius: float = DEFAULT_TEMPERATURE_CELSIUS
    water_clarity: str = DEFAULT_WATER_CLARITY
    notes: str = ''
    is_readonly: bool = False
    is_existing: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for UI binding."""
        return {
            'hotel': self.hotel,
            'status': self.status,
            'ph_level': self.ph_level,
            'chlorine_ppm': self.chlorine_ppm,
            'alkalinity_ppm': self.alkalinity_ppm,
            'temperature_celsius': self.temperature_celsius,
            'water_clarity': self.water_clarity,
            'notes': self.notes,
            'is_readonly': self.is_readonly,
            'is_existing': self.is_existing,
        }


class PoolFormComponent:
    """Component for rendering the pool inspection form."""

    def __init__(self, user: User, reading_ref_id: Optional[str] = None):
        """
        Initialize the pool form component.

        Args:
            user: The authenticated user
            reading_ref_id: Optional reference ID for editing existing reading
        """
        self.user = user
        self.reading_ref_id = reading_ref_id
        self.state: dict = FormState().to_dict()

    async def load_data(self) -> None:
        """Load form data from database if editing existing reading."""
        # Load hotel name for the current user
        self.state['hotel'] = await self._get_user_hotel_name()

        # If no reference ID, this is a new form
        if not self.reading_ref_id:
            return

        # Load existing reading data
        try:
            reading = await self._fetch_reading_from_db()
            self._populate_state_from_reading(reading)
        except PoolReading.DoesNotExist:
            logger.error(f"Reading not found: {self.reading_ref_id}")
            ui.notify(
                f'Reading {self.reading_ref_id} not found',
                type='negative'
            )

    @sync_to_async
    def _get_user_hotel_name(self) -> str:
        """Get the hotel name for the current user."""
        return self.user.hotel.name if self.user.hotel else ''

    async def _fetch_reading_from_db(self) -> PoolReading:
        """Fetch reading from database by reference ID."""
        return await PoolReading.objects.select_related('hotel').aget(
            reference_id=self.reading_ref_id
        )

    def _populate_state_from_reading(self, reading: PoolReading) -> None:
        """Populate form state from database reading."""
        self.state.update({
            'hotel': reading.hotel.name,
            'status': reading.status,
            'ph_level': float(reading.ph_level),
            'chlorine_ppm': float(reading.chlorine_ppm),
            'alkalinity_ppm': reading.alkalinity_ppm,
            'temperature_celsius': float(reading.temperature_celsius),
            'water_clarity': reading.water_clarity,
            'notes': reading.notes,
            'is_existing': True,
            'is_readonly': reading.status in READONLY_STATUSES
        })

    async def handle_submit(self, msg_label: ui.label) -> None:
        """
        Handle form submission.

        Args:
            msg_label: UI label to display submission result
        """
        result = await self._submit_form()

        if result.success:
            self._handle_success(result, msg_label)
        else:
            self._handle_error(result, msg_label)

    async def _submit_form(self) -> PoolReadingSubmissionResult:
        """Submit form data to the backend service."""
        return await submit_pool_reading(
            ph_level=self.state['ph_level'],
            chlorine_ppm=self.state['chlorine_ppm'],
            alkalinity_ppm=self.state['alkalinity_ppm'],
            temperature_celsius=self.state['temperature_celsius'],
            water_clarity=self.state['water_clarity'],
            notes=self.state['notes'],
            user=self.user,
        )

    def _handle_success(
        self,
        result: PoolReadingSubmissionResult,
        msg_label: ui.label
    ) -> None:
        """Handle successful form submission."""
        self.state['status'] = 'submitted'
        msg_label.text = f"✓ Başarılı! Referans: {result.reference_id}"
        msg_label.classes('text-green-600')
        logger.info(f"Form submitted successfully: {result.reference_id}")

    def _handle_error(
        self,
        result: PoolReadingSubmissionResult,
        msg_label: ui.label
    ) -> None:
        """Handle form submission error."""
        msg_label.text = f"✗ Hata: {result.message}"
        msg_label.classes('text-red-600')
        logger.error(f"Form submission failed: {result.message}")

    # --- UI Rendering Methods ---

    def _render_navbar(self) -> None:
        """Render the top navigation bar."""
        with ui.header().classes('bg-blue-600 text-white p-4'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('Havuz Denetim Sistemi').classes('text-h5 font-bold')
                with ui.row().classes('gap-4'):
                    ui.button(
                        'Kontrol Paneli',
                        on_click=lambda: ui.navigate.to(ROUTE_SUBMISSIONS)
                    ).props('flat').classes('text-white')
                    ui.button(
                        'Form Doldur',
                        on_click=lambda: ui.navigate.to(ROUTE_FORM_NEW)
                    ).props('flat').classes('text-white')
                    ui.label(f'Kullanıcı: {self.user.username}').classes('text-white ml-4')

    def _render_header(self) -> None:
        """Render the form header section."""
        title = (
            f'Ölçüm Görüntüleniyor: {self.reading_ref_id}'
            if self.reading_ref_id
            else 'Yeni Havuz Ölçümü'
        )
        ui.label(title).classes('text-h3 mb-4')
        ui.label(
            f'Kullanıcı: {self.user.username}'
        ).classes('text-subtitle1 mb-6 text-gray-600')

    def _render_status_field(self) -> None:
        """Render the status selection field."""
        ui.label('Gönderim Durumu').classes('text-h6 mt-4 mb-2')

        status_select = ui.select(
            options=dict(PoolReading.Status.choices),
            label='Durum'
        ).bind_value(self.state, 'status').classes('w-full')

        # Only admins can change status
        if not self.user.is_admin:
            status_select.disable()
            status_select.props('readonly')

    def _render_hotel_info(self) -> None:
        """Render the hotel information section."""
        ui.label('Otel Bilgileri').classes('text-h6 mt-4 mb-2')
        ui.input('Otel Adı').bind_value(
            self.state, 'hotel'
        ).props('readonly').classes('w-full bg-gray-100')

    def _render_chemical_readings(self) -> None:
        """Render the chemical readings input section."""
        ui.label('Kimyasal Ölçümler').classes('text-h6 mt-6 mb-2')

        with ui.row().classes('w-full gap-4'):
            self._create_number_input(
                label='pH Seviyesi',
                key='ph_level',
                min_val=PH_MIN,
                max_val=PH_MAX,
                step=PH_STEP
            )
            self._create_number_input(
                label='Klor (ppm)',
                key='chlorine_ppm',
                min_val=CHLORINE_MIN,
                max_val=None,
                step=CHLORINE_STEP
            )

        with ui.row().classes('w-full gap-4'):
            self._create_number_input(
                label='Alkalinite (ppm)',
                key='alkalinity_ppm',
                min_val=ALKALINITY_MIN,
                max_val=None,
                step=ALKALINITY_STEP
            )
            self._create_number_input(
                label='Sıcaklık (°C)',
                key='temperature_celsius',
                min_val=TEMPERATURE_MIN,
                max_val=None,
                step=TEMPERATURE_STEP
            )

    def _create_number_input(
        self,
        label: str,
        key: str,
        min_val: float,
        max_val: Optional[float],
        step: float
    ) -> ui.number:
        """
        Create a number input field with consistent styling.

        Args:
            label: Field label
            key: State dictionary key to bind to
            min_val: Minimum allowed value
            max_val: Maximum allowed value (None for no limit)
            step: Step increment for the input

        Returns:
            The created number input element
        """
        precision = 1 if step < 1 else None

        return ui.number(
            label,
            min=min_val,
            max=max_val,
            step=step,
            precision=precision
        ).bind_value(
            self.state, key
        ).bind_enabled_from(
            self.state, 'is_readonly', backward=lambda x: not x
        ).classes('flex-1')

    def _render_water_quality(self) -> None:
        """Render the water quality selection field."""
        ui.label('Su Kalitesi').classes('text-h6 mt-6 mb-2')

        ui.select(
            options=dict(PoolReading.WaterClarity.choices),
            label='Su Berraklığı'
        ).bind_value(
            self.state, 'water_clarity'
        ).bind_enabled_from(
            self.state, 'is_readonly', backward=lambda x: not x
        ).classes('w-full')

    def _render_notes(self) -> None:
        """Render the notes textarea field."""
        ui.label('Ek Notlar').classes('text-h6 mt-6 mb-2')

        ui.textarea('Notlar').bind_value(
            self.state, 'notes'
        ).bind_enabled_from(
            self.state, 'is_readonly', backward=lambda x: not x
        ).classes('w-full')

    def _render_actions(self) -> None:
        """Render the form action buttons."""
        message_label = ui.label('').classes('w-full text-center mt-4 font-bold')

        show_submit = (not self.state['is_readonly']) or self.user.is_admin

        if show_submit:
            ui.button(
                'Gönder / Güncelle',
                on_click=lambda: self.handle_submit(message_label)
            ).classes('w-full mt-6 bg-blue-600')
        else:
            ui.button(
                'Kontrol Paneline Dön',
                on_click=lambda: ui.navigate.to(ROUTE_SUBMISSIONS)
            ).classes('w-full mt-6 bg-gray-500')

    async def render(self) -> None:
        """Render the complete pool form page."""
        await self.load_data()

        self._render_navbar()

        with ui.column().classes('w-full max-w-2xl mx-auto p-8'):
            self._render_header()
            self._render_status_field()
            self._render_hotel_info()
            self._render_chemical_readings()
            self._render_water_quality()
            self._render_notes()
            self._render_actions()


async def render_pool_form(user: User, reading_ref_id: Optional[str] = None) -> None:
    """
    Render the pool reading form page.

    This is the main entry point used by the router.

    Args:
        user: The authenticated user
        reading_ref_id: Optional reference ID for editing existing reading
    """
    form = PoolFormComponent(user, reading_ref_id)
    await form.render()
