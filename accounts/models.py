from django.db import models


class User(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    hotel = models.ForeignKey('hotels.Hotel', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def __str__(self) -> str:
        return self.username
