from django.db import models
from accounts.models import User
from datetime import datetime


class PoolReading(models.Model):
    class WaterClarity(models.TextChoices):
        CLEAR = 'clear', 'Berrak'
        CLOUDY = 'cloudy', 'Bulanık'
        ALGAE = 'algae', 'Yosun Var'

    class Status(models.TextChoices):
        OPEN = 'open', 'Açık'
        SUBMITTED = 'submitted', 'Gönderildi'
        IN_PROGRESS = 'in_progress', 'İnceleniyor'
        COMPLETED = 'completed', 'Tamamlandı'

    # Metadata
    hotel = models.ForeignKey('hotels.Hotel', on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)

    # Chemical readings
    ph_level = models.DecimalField(max_digits=3, decimal_places=1, help_text="pH Level (6.0-8.0)")
    chlorine_ppm = models.DecimalField(max_digits=4, decimal_places=1, help_text="Free Chlorine (ppm)")
    alkalinity_ppm = models.IntegerField(help_text="Total Alkalinity (ppm)")
    temperature_celsius = models.DecimalField(max_digits=4, decimal_places=1, help_text="Water Temperature (°C)")
    water_clarity = models.CharField(
        max_length=20,
        choices=WaterClarity.choices,
    )
    notes = models.TextField(blank=True, null=True)
    reference_id = models.CharField(max_length=500, unique=True, editable=False, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    class Meta:
        ordering = ['-submission_date']

    def save(self, *args, **kwargs) -> None:
        # Auto-generate reference_id: HOTELNAME__USERNAME__DATETIME
        if not self.reference_id:
            timestamp = self.submission_date.strftime('%Y%m%d_%H%M%S') if self.submission_date else datetime.now().strftime('%Y%m%d_%H%M%S')
            self.reference_id = f"{self.hotel.name}__{self.submitted_by.username}__{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.hotel.name} - {self.submission_date.strftime('%Y-%m-%d')}"
