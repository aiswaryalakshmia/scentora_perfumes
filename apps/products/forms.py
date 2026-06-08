from django import forms
from .models import Category,Product, ProductVariant

class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['category_name', 'description', 'image']

        widgets = {
            'category_name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter category name'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Enter description'
                }
            ),
        }

    def clean_category_name(self):

        name = self.cleaned_data.get('category_name')

        queryset = Category.objects.filter(
            category_name__iexact=name
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
        )

        if queryset.exists():
            raise forms.ValidationError(
                "Category already exists."
        )

        return name
    
class ProductForm(forms.ModelForm):

    class Meta:

        model = Product

        fields = [
            'product_name',
            'category',
            'description'
        ]

        widgets = {

            'product_name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter product name'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'rows': 5,
                    'placeholder': 'Enter product description'
                }
            )

        }

    def clean_product_name(self):

        product_name = self.cleaned_data["product_name"]

        existing_product = Product.objects.filter(
            product_name__iexact=product_name
        ).exclude(
            id=self.instance.id
        )

        if existing_product.exists():

            raise forms.ValidationError(
                "Product already exists."
            )

        return product_name 

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size', 'price', 'stock']

    def clean_size(self):

        size = self.cleaned_data['size']

        if size <= 0:

            raise forms.ValidationError(
                "Size must be greater than 0 ml."
            )

        if size > 1000:

            raise forms.ValidationError(
                "Size cannot exceed 1000 ml."
            )

        return size

    def clean_price(self):

        price = self.cleaned_data['price']

        if price <= 0:

            raise forms.ValidationError(
                "Price must be greater than 0."
            )

        return price

    def clean_stock(self):

        stock = self.cleaned_data['stock']

        if stock < 0:

            raise forms.ValidationError(
                "Stock cannot be negative."
            )

        return stock
