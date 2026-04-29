from django.db import models

class Message(models.Model):
    phone_number = models.CharField(max_length=15)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number
