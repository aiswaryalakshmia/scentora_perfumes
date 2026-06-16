from django import forms
from .models import Category, Product, ProductVariant


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

        if not name or not name.strip():
            raise forms.ValidationError("Category name cannot be empty.")
        if len(name) < 3:
            raise forms.ValidationError("Category name must be at least 3 characters.")
        if len(name) > 100:
            raise forms.ValidationError("Category name cannot exceed 100 characters.")
        if not name.replace(' ', '').isalpha():
            raise forms.ValidationError("Category name can only contain letters.")

        queryset = Category.objects.filter(category_name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Category already exists.")

        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')

        if not description or not description.strip():
            raise forms.ValidationError("Description cannot be empty.")
        if len(description) < 10:
            raise forms.ValidationError("Description must be at least 10 characters.")
        if len(description) > 500:
            raise forms.ValidationError("Description cannot exceed 500 characters.")

        return description

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            raise forms.ValidationError("Category image is required.")

        return image


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ['product_name', 'category', 'description']

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
        product_name = self.cleaned_data.get('product_name')

        if not product_name or not product_name.strip():
            raise forms.ValidationError("Product name cannot be empty.")
        if len(product_name) < 3:
            raise forms.ValidationError("Product name must be at least 3 characters.")
        if len(product_name) > 200:
            raise forms.ValidationError("Product name cannot exceed 200 characters.")

        existing_product = Product.objects.filter(
            product_name__iexact=product_name
        ).exclude(id=self.instance.id)

        if existing_product.exists():
            raise forms.ValidationError("Product already exists.")

        return product_name

    def clean_description(self):
        description = self.cleaned_data.get('description')

        if not description or not description.strip():
            raise forms.ValidationError("Description cannot be empty.")
        if len(description) < 10:
            raise forms.ValidationError("Description must be at least 10 characters.")
        if len(description) > 1000:
            raise forms.ValidationError("Description cannot exceed 1000 characters.")

        return description

    def clean_category(self):
        category = self.cleaned_data.get('category')

        if not category:
            raise forms.ValidationError("Please select a category.")

        return category


class ProductVariantForm(forms.ModelForm):

    class Meta:
        model = ProductVariant
        fields = ['size', 'price', 'discount_price', 'stock']

    def clean_size(self):
        size = self.cleaned_data.get('size')

        if size is None:
            raise forms.ValidationError("Size is required.")
        if size <= 0:
            raise forms.ValidationError("Size must be greater than 0 ml.")
        if size > 1000:
            raise forms.ValidationError("Size cannot exceed 1000 ml.")

        return size

    def clean_price(self):
        price = self.cleaned_data.get('price')

        if price is None:
            raise forms.ValidationError("Price is required.")
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        if price > 100000:
            raise forms.ValidationError("Price cannot exceed ₹1,00,000.")

        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')

        if stock is None:
            raise forms.ValidationError("Stock is required.")
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        if stock > 10000:
            raise forms.ValidationError("Stock cannot exceed 10,000.")

        return stock