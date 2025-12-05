"""Pool reading service for managing pool inspection submissions."""

from typing import Optional
import logging

from pydantic import BaseModel, Field

from models import User, PoolReading


logger = logging.getLogger(__name__)


class PoolReadingSubmissionResult(BaseModel):
    """
    Result of a pool reading submission operation.

    Attributes:
        success: Whether the submission was successful
        message: Human-readable message about the result
        reference_id: Unique reference ID for the submitted reading (if successful)
        reading: The created PoolReading instance (if successful)
    """
    success: bool
    message: str
    reference_id: Optional[str] = None
    reading: Optional[PoolReading] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True


class PoolReadingData(BaseModel):
    """
    Data transfer object for pool reading submission.

    Attributes:
        ph_level: pH measurement (0-14)
        chlorine_ppm: Free chlorine in parts per million
        alkalinity_ppm: Total alkalinity in parts per million
        temperature_celsius: Water temperature in Celsius
        water_clarity: Visual clarity assessment
        notes: Additional notes or observations
    """
    ph_level: float = Field(ge=0.0, le=14.0, description="pH Level (0-14)")
    chlorine_ppm: float = Field(ge=0.0, description="Free Chlorine (ppm)")
    alkalinity_ppm: int = Field(ge=0, description="Total Alkalinity (ppm)")
    temperature_celsius: float = Field(description="Water Temperature (°C)")
    water_clarity: str = Field(description="Visual clarity assessment")
    notes: str = Field(default="", description="Additional notes")


class PoolReadingService:
    """Service for managing pool reading operations."""

    @staticmethod
    async def submit_reading(
        data: PoolReadingData,
        user: User
    ) -> PoolReadingSubmissionResult:
        """
        Submit a new pool reading.

        Args:
            data: The pool reading data to submit
            user: The user submitting the reading

        Returns:
            PoolReadingSubmissionResult with success status and details
        """
        try:
            # Validate user has associated hotel
            if not user.hotel:
                return PoolReadingSubmissionResult(
                    success=False,
                    message="Kullanıcı bir otelle ilişkilendirilmemiş. "
                            "Lütfen yöneticiyle iletişime geçin."
                )

            # Create the pool reading
            reading = await PoolReadingService._create_reading(data, user)

            # Refresh to get auto-generated fields
            await reading.arefresh_from_db()

            logger.info(
                f"Pool reading submitted successfully: {reading.reference_id} "
                f"by user {user.username}"
            )

            return PoolReadingSubmissionResult(
                success=True,
                message=f"Havuz ölçümü başarıyla gönderildi.",
                reference_id=reading.reference_id,
                reading=reading
            )

        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error during submission: {e}")
            return PoolReadingSubmissionResult(
                success=False,
                message=f"Doğrulama hatası: {str(e)}"
            )

        except Exception as e:
            # Unexpected errors
            logger.error(
                f"Database error during form submission by {user.username}: {e}",
                exc_info=True
            )
            return PoolReadingSubmissionResult(
                success=False,
                message=f"Sistem hatası nedeniyle gönderim başarısız oldu. "
                        f"Lütfen daha sonra tekrar deneyin."
            )

    @staticmethod
    async def _create_reading(data: PoolReadingData, user: User) -> PoolReading:
        """
        Create a new pool reading in the database.

        Args:
            data: The pool reading data
            user: The user submitting the reading

        Returns:
            The created PoolReading instance
        """
        return await PoolReading.objects.acreate(
            hotel=user.hotel,
            submitted_by=user,
            ph_level=data.ph_level,
            chlorine_ppm=data.chlorine_ppm,
            alkalinity_ppm=data.alkalinity_ppm,
            temperature_celsius=data.temperature_celsius,
            water_clarity=data.water_clarity,
            notes=data.notes,
            status=PoolReading.Status.SUBMITTED
        )

    @staticmethod
    async def get_reading_by_reference(
        reference_id: str
    ) -> Optional[PoolReading]:
        """
        Retrieve a pool reading by its reference ID.

        Args:
            reference_id: The reference ID to look up

        Returns:
            The PoolReading instance if found, None otherwise
        """
        try:
            return await PoolReading.objects.select_related(
                'hotel',
                'submitted_by'
            ).aget(reference_id=reference_id)
        except PoolReading.DoesNotExist:
            logger.warning(f"Pool reading not found: {reference_id}")
            return None

    @staticmethod
    async def update_reading_status(
        reading: PoolReading,
        new_status: str,
        updated_by: User
    ) -> bool:
        """
        Update the status of a pool reading.

        Args:
            reading: The pool reading to update
            new_status: The new status value
            updated_by: The user making the update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate status
            if new_status not in dict(PoolReading.Status.choices):
                raise ValueError(f"Invalid status: {new_status}")

            reading.status = new_status
            await reading.asave(update_fields=['status'])

            logger.info(
                f"Reading {reading.reference_id} status updated to "
                f"{new_status} by {updated_by.username}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating reading status: {e}", exc_info=True)
            return False


# Convenience function for backward compatibility
async def submit_pool_reading(
    ph_level: float,
    chlorine_ppm: float,
    alkalinity_ppm: int,
    temperature_celsius: float,
    water_clarity: str,
    notes: str,
    user: User
) -> PoolReadingSubmissionResult:
    """
    Submit a new pool reading (legacy function signature).

    This function maintains backward compatibility with existing code.
    Consider using PoolReadingService.submit_reading() directly for new code.

    Args:
        ph_level: pH measurement
        chlorine_ppm: Free chlorine in ppm
        alkalinity_ppm: Total alkalinity in ppm
        temperature_celsius: Water temperature in Celsius
        water_clarity: Visual clarity assessment
        notes: Additional notes
        user: The user submitting the reading

    Returns:
        PoolReadingSubmissionResult with success status and details
    """
    data = PoolReadingData(
        ph_level=ph_level,
        chlorine_ppm=chlorine_ppm,
        alkalinity_ppm=alkalinity_ppm,
        temperature_celsius=temperature_celsius,
        water_clarity=water_clarity,
        notes=notes
    )
    return await PoolReadingService.submit_reading(data, user)
