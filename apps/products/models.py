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

class Product(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE
    )

    product_name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return str(self.product_name)

class ProductVariant(models.Model):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive')
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    size = models.PositiveIntegerField()     
    

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField()    

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'size'],
                name='unique_product_size'
            )
        ]

    def __str__(self):
        return f"{self.product.product_name} - {self.size}"

class VariantImage(models.Model):

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='variant_images/'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )  
    
    def __str__(self):
        return str(self.image)
