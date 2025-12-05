"""Login form page component for user authentication."""

from typing import Callable
import logging

from nicegui import ui

from models import User
from services.auth import AuthenticationResult, authenticate_user
from ui.navigation import ROUTE_SUBMISSIONS


logger = logging.getLogger(__name__)


# Constants
DEFAULT_USERNAME = 'john_plaza'  # For development only
DEFAULT_PASSWORD = 'admin'  # For development only
REDIRECT_AFTER_LOGIN = ROUTE_SUBMISSIONS


class LoginFormComponent:
    """Component for rendering the login form page."""

    def __init__(self, on_success_callback: Callable[[User], None]):
        """
        Initialize the login form component.

        Args:
            on_success_callback: Callback function to execute on successful login
        """
        self.on_success_callback = on_success_callback
        self.username_input: ui.input = None
        self.password_input: ui.input = None
        self.message_label: ui.label = None

    async def handle_login(self) -> None:
        """Handle login form submission."""
        username = self.username_input.value
        password = self.password_input.value

        # Validate inputs
        if not username or not password:
            self._show_error("Lütfen kullanıcı adı ve şifre girin")
            return

        # Authenticate
        result = await self._authenticate(username, password)

        if result.success:
            self._handle_success(result)
        else:
            self._handle_error(result)

    async def _authenticate(self, username: str, password: str) -> AuthenticationResult:
        """
        Authenticate user credentials.

        Args:
            username: The username to authenticate
            password: The password to authenticate

        Returns:
            AuthenticationResult with success status and user or error message
        """
        try:
            return await authenticate_user(username, password)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthenticationResult(
                success=False,
                message="Kimlik doğrulama sırasında bir hata oluştu",
                user=None
            )

    def _handle_success(self, result: AuthenticationResult) -> None:
        """
        Handle successful login.

        Args:
            result: The successful authentication result
        """
        logger.info(f"User logged in successfully: {result.user.username}")

        self.message_label.text = result.message
        self.message_label.classes('text-green-600')

        # Execute callback to store user session
        self.on_success_callback(result.user)

        # Redirect to dashboard
        ui.navigate.to(REDIRECT_AFTER_LOGIN)

    def _handle_error(self, result: AuthenticationResult) -> None:
        """
        Handle login failure.

        Args:
            result: The failed authentication result
        """
        logger.warning(f"Failed login attempt: {result.message}")

        self.message_label.text = result.message
        self.message_label.classes('text-red-600')

    def _show_error(self, message: str) -> None:
        """
        Display an error message.

        Args:
            message: The error message to display
        """
        self.message_label.text = message
        self.message_label.classes('text-red-600')

    def _render_card(self) -> None:
        """Render the login card with form fields."""
        with ui.card().classes('absolute-center w-96 p-8 shadow-lg'):
            self._render_header()
            self._render_form_fields()
            self._render_message()
            self._render_submit_button()

    def _render_header(self) -> None:
        """Render the login form header."""
        ui.label('Havuz Denetim Sistemi').classes('text-h5 w-full text-center mb-2')
        ui.label('Giriş').classes('text-h4 w-full text-center mb-4 font-bold')

    def _render_form_fields(self) -> None:
        """Render username and password input fields."""
        self.username_input = ui.input(
            'Kullanıcı Adı',
            value=DEFAULT_USERNAME,
            placeholder='Kullanıcı adınızı girin'
        ).classes('w-full mb-2').on('keydown.enter', lambda: self.handle_login())

        self.password_input = ui.input(
            'Şifre',
            password=True,
            value=DEFAULT_PASSWORD,
            placeholder='Şifrenizi girin'
        ).classes('w-full').on('keydown.enter', lambda: self.handle_login())

    def _render_message(self) -> None:
        """Render the message label for feedback."""
        self.message_label = ui.label('').classes('w-full text-center mt-2 min-h-6')

    def _render_submit_button(self) -> None:
        """Render the login submit button."""
        ui.button(
            'Giriş Yap',
            on_click=lambda: self.handle_login()
        ).classes('w-full mt-4 bg-blue-600')

    def render(self) -> None:
        """Render the complete login page."""
        self._render_card()


def render_login_form(on_success_callback: Callable[[User], None]) -> None:
    """
    Render the login form page.

    This is the main entry point used by the router.

    Args:
        on_success_callback: Callback function to execute on successful login,
                            receives the authenticated User object
    """
    component = LoginFormComponent(on_success_callback)
    component.render()
