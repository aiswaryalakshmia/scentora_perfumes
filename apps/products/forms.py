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
            'description',
            'status'
        ]


class ProductVariantForm(forms.ModelForm):

    class Meta:
        model = ProductVariant
        fields = [
            'size',
            'price',
            'stock',
            'image'
        ]