from django.db import models

class Category(models.Model):
    STATUS_CHOICES = (
        ('active','Active'),
        ('inactive','Inactive')
    )

    category_name = models.CharField(max_length=20,unique=True)

    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to = 'category_images/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.category_name)
