from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.files.base import ContentFile
from .models import Category,Product,ProductVariant,VariantImage
from .forms import CategoryForm,ProductForm, ProductVariantForm
import json
import base64

def category_management(request):
    search_query = request.GET.get('search','').strip()
    categories = Category.objects.order_by('-created_at')

    if search_query:
        categories = categories.filter(
            Q(category_name__icontains=search_query)|
            Q(description__icontains=search_query)
        )

    paginator=Paginator(categories,5)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)

    return render(
        request,
        'admin/category_management.html',
        {
            'categories': page_obj,
            'search_query': search_query
        }
    )

def add_category(request):

    # If user submitted form
    if request.method == 'POST':
        form = CategoryForm(request.POST,request.FILES)
        
        if form.is_valid():
            form.save()   # Save the data to database
            messages.success(
                request,
                "Category added successfully!"
            )
           
            return redirect('category_management')

    # If user just opened page
    else:
        form = CategoryForm()

    return render(request, 'admin/add_category.html', {'form': form})

def edit_category(request,category_id):
    category = get_object_or_404(
        Category,
        id=category_id
    )

    if request.method == 'POST':
        form=CategoryForm(request.POST,request.FILES,instance=category)

        if form.is_valid():
            form.save()

            messages.success(request,"Category updated successfully!")
            return redirect('category_management')

    else:
        form=CategoryForm(instance=category)

    return render(
        request,
        'admin/edit_category.html',
        {
            'form':form,
            'category':category
        }
    )

def toggle_category_status(request, category_id):
    category=get_object_or_404(
        Category,
        id=category_id
    )

    if category.status == 'active':
        category.status = 'inactive'

        messages.success(
            request,
            f'{category.category_name} blocked successfully.'
        )

    else:
        category.status = 'active'

        messages.success(
            request,
            f'{category.category_name} unblocked successfully.'
        )
    category.save()

    return redirect('category_management')

def product_management(request):

    search_query = request.GET.get('search', '')
    product_list = Product.objects.select_related('category').order_by("-created_at")

    if search_query:
        product_list = product_list.filter(
            Q(product_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__category_name__icontains=search_query)
        )

    paginator = Paginator(product_list, 5)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'admin/product_management.html', {
        'products': products,
        'search_query': search_query
    })

def add_product(request):

    categories = Category.objects.all()

    if request.method == "POST":
        product = Product.objects.create(
            product_name=request.POST['product_name'],
            description=request.POST['description'],
            category_id=request.POST['category']
        )

        messages.success(
            request,
            "Product added successfully."
        )

        return redirect('add_variant', product_id=product.id)

    return render(request, 'admin/add_product.html', {
        'categories': categories
    })

def add_variant(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductVariantForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            variant = form.save(commit=False)
            variant.product = product
            variant.save()

            # Get cropped images JSON
            cropped_images = request.POST.get("cropped_images")

            if cropped_images:

                try:

                    images = json.loads(cropped_images)

                    for index, image_data in enumerate(images):

                        format_data, imgstr = image_data.split(";base64,")

                        ext = format_data.split("/")[-1]

                        image_file = ContentFile(
                            base64.b64decode(imgstr),
                            name=f"variant_{variant.id}_{index}.{ext}"
                        )

                        VariantImage.objects.create(
                            variant=variant,
                            image=image_file
                        )

                except Exception as e:

                    print("Image processing error:", e)

                    messages.error(
                        request,
                        "Error while processing images."
                    )

            messages.success(
                request,
                "Variant added successfully."
            )

            # Coming from Edit Product page
            if "add_product_variant" in request.POST:

                return redirect(
                    "edit_product",
                    product_id=product.id
                )

            # Coming from Add Variant page
            return redirect(
                "add_variant",
                product_id=product.id
            )

    else:

        form = ProductVariantForm()

    variants = ProductVariant.objects.filter(
        product=product
    )

    return render(
        request,
        "admin/add_variant.html",
        {
            "product": product,
            "form": form,
            "variants": variants,
        }
    )

def edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            instance=product
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Product updated successfully."
            )

            return redirect(
                'edit_product',
                product_id=product.id
            )

    else:

        form = ProductForm(
            instance=product
        )

    variants = ProductVariant.objects.filter(
        product=product
    )

    return render(
        request,
        'admin/edit_product.html',
        {
            'product': product,
            'form': form,
            'variants': variants
        }
    )

def update_variant(request, variant_id):

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id
    )

    if request.method == "POST":

        variant.size = request.POST.get("size")
        variant.price = request.POST.get("price")
        variant.stock = request.POST.get("stock")

        variant.save()

        # Cropped images from Cropper.js
        cropped_images = request.POST.get("cropped_images")

        if cropped_images:

            try:

                images = json.loads(cropped_images)

                for index, image_data in enumerate(images):

                    format_data, imgstr = image_data.split(";base64,")

                    ext = format_data.split("/")[-1]

                    image_file = ContentFile(
                        base64.b64decode(imgstr),
                        name=f"variant_{variant.id}_{index}.{ext}"
                    )

                    VariantImage.objects.create(
                        variant=variant,
                        image=image_file
                    )

            except Exception as e:

                print("Crop image error:", e)

                messages.error(
                    request,
                    "Error while processing cropped images."
                )

        messages.success(
            request,
            "Variant updated successfully."
        )

    return redirect(
        "edit_product",
        product_id=variant.product.id
    )

def delete_variant_image(request, image_id):

    image = get_object_or_404(
        VariantImage,
        id=image_id
    )

    product_id = image.variant.product.id

    image.delete()

    messages.success(
        request,
        "Image deleted successfully."
    )

    return redirect(
        "edit_product",
        product_id=product_id
    )

def toggle_product_status(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if product.status == "active":
        product.status = "inactive"
    else:
        product.status = "active"

    product.save()

    return redirect('product_management')

def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    product_id = variant.product.id  # to redirect back
    variant.delete()

    messages.success(
        request,
        "Variant deleted successfully."
    )

    return redirect('edit_product', product_id=product_id)

def shop(request):
    return render(request,'user/shop_page.html')
