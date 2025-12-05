"""Authentication and user management service."""

from typing import Optional
import logging

from django.contrib.auth.hashers import check_password
from pydantic import BaseModel
from nicegui import app

from models import User


logger = logging.getLogger(__name__)


# Constants
SESSION_USER_ID_KEY = 'user_id'


class AuthenticationResult(BaseModel):
    """Result of an authentication attempt."""
    success: bool
    message: str
    user: Optional[User] = None

    class Config:
        arbitrary_types_allowed = True


class AuthenticationService:
    """Service for managing user authentication and sessions."""

    @staticmethod
    async def authenticate(
        username: str,
        password: str
    ) -> AuthenticationResult:
        """
        Authenticate a user with username and password.

        Args:
            username: The username to authenticate
            password: The plaintext password to verify

        Returns:
            AuthenticationResult with success status and user or error message
        """
        if not username or not password:
            return AuthenticationResult(
                success=False,
                message="Kullanıcı adı ve şifre gereklidir"
            )

        try:
            user = await User.objects.select_related('hotel').aget(
                username=username
            )

            if check_password(password, user.password_hash):
                logger.info(f"Successful authentication for user: {username}")
                return AuthenticationResult(
                    success=True,
                    message="Giriş başarılı!",
                    user=user
                )
            else:
                logger.warning(f"Failed authentication for user: {username}")
                return AuthenticationResult(
                    success=False,
                    message="Geçersiz şifre"
                )

        except User.DoesNotExist:
            logger.warning(f"Authentication attempt for non-existent user: {username}")
            return AuthenticationResult(
                success=False,
                message="Kullanıcı bulunamadı"
            )

        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}", exc_info=True)
            return AuthenticationResult(
                success=False,
                message="Kimlik doğrulama sırasında bir hata oluştu"
            )

    @staticmethod
    async def get_current_user() -> Optional[User]:
        """
        Retrieve the currently logged-in user from the session.

        Returns:
            The authenticated User object, or None if not logged in
        """
        user_id = app.storage.user.get(SESSION_USER_ID_KEY)

        if not user_id:
            return None

        try:
            user = await User.objects.select_related('hotel').aget(id=user_id)
            return user

        except User.DoesNotExist:
            logger.warning(f"Stale session detected for user_id={user_id}")
            AuthenticationService.clear_session()
            return None

        except Exception as e:
            logger.error(f"Error retrieving current user: {e}", exc_info=True)
            return None

    @staticmethod
    def store_user_session(user: User) -> None:
        """Store user ID in the session."""
        app.storage.user[SESSION_USER_ID_KEY] = user.id
        logger.debug(f"Session created for user: {user.username}")

    @staticmethod
    def clear_session() -> None:
        """Clear the current user session."""
        app.storage.user.clear()
        logger.debug("Session cleared")


# Convenience functions for backward compatibility
async def authenticate_user(username: str, password: str) -> AuthenticationResult:
    """Authenticate user (legacy function)."""
    return await AuthenticationService.authenticate(username, password)


async def get_current_user() -> Optional[User]:
    """Get current user from session (legacy function)."""
    return await AuthenticationService.get_current_user()
