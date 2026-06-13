import json
import base64
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.files.base import ContentFile
from .models import Category,Product,ProductVariant,VariantImage,Cart,CartItem
from .forms import CategoryForm,ProductForm, ProductVariantForm
from django.contrib.auth.decorators import login_required

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

    total_products = Product.objects.count()

    active_products = Product.objects.filter(
        status='active'
    ).count()

    blocked_products = Product.objects.filter(
        status='inactive'
    ).count()

    out_of_stock_products = Product.objects.filter(
    variants__stock=0
    ).distinct().count()

    paginator = Paginator(product_list, 5)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'admin/product_management.html', {
        'products': products,
        'search_query': search_query,
        'total_products': total_products,
        'active_products': active_products,
        'blocked_products': blocked_products,
        'out_of_stock_products': out_of_stock_products,
    })

def add_product(request):

    if request.method == "POST":
        form = ProductForm(request.POST)

        if form.is_valid():

            product = form.save()

            messages.success(
                request,
                "Product added successfully."
            )

            return redirect('add_variant', product_id=product.id)

    else:

        form = ProductForm()

    return render(request, 'admin/add_product.html', {
        'form': form
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

            # Get cropped images JSON
            cropped_images = request.POST.get("cropped_images")

            if not cropped_images:
                messages.error(
                    request,
                    "Please upload at least 3 images."
                )
                return redirect(
                    "add_variant",
                    product_id=product.id
                )

            try:
                images = json.loads(cropped_images)

                if len(images) < 3:
                    messages.error(
                        request,
                        "Please upload at least 3 images."
                    )
                    return redirect(
                        "add_variant",
                        product_id=product.id
                    )

            except Exception:
                messages.error(
                    request,
                    "Invalid image data."
                )
                return redirect(
                    "add_variant",
                    product_id=product.id
                )

            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            
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

        form = ProductVariantForm(
            request.POST,
            instance=variant
        )

        if form.is_valid():

            variant = form.save()

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
        else:
            for field, errors in form.errors.get_json_data().items():

                for error in errors:

                    messages.error(
                        request,
                        error["message"]
                    )

            return redirect(
                "edit_product",
                product_id=variant.product.id
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

    variants = ProductVariant.objects.filter(
        status = 'active',
        product__status = 'active',
        product__category__status = 'active'
    )
    selected_categories = request.GET.getlist('category')

    if selected_categories:
        variants = variants.filter(
            product__category__category_name__in=selected_categories
        )

    selected_price = request.GET.get('price')

    if selected_price == 'under_3000':
        variants = variants.filter(price__lt=3000)

    elif selected_price == '3000_5000':
        variants = variants.filter(
            price__gte=3000,
            price__lte=5000
        )

    elif selected_price == '5000_8000':
        variants = variants.filter(
        price__gte=5000,
        price__lte=8000
    )

    elif selected_price == 'above_8000':
        variants = variants.filter(price__gt=8000)

    search_query = request.GET.get('search','')
    if search_query:
        variants = variants.filter(
            product__product_name__icontains=search_query
        )

    sort = request.GET.get('sort')
    if sort == 'price_low':
        variants = variants.order_by('price')
    elif sort == 'price_high':
        variants = variants.order_by('-price')
    elif sort == 'a_z':
        variants = variants.order_by('product__product_name')
    elif sort == 'z_a':
        variants = variants.order_by('-product__product_name')

    paginator = Paginator(variants, 9)  # 9 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(
        status='active'
    )
    return render(request,'user/shop_page.html',
                  {
                      'variants':variants,
                      'categories':categories,
                      'selected_categories': selected_categories,
                      'selected_price': selected_price,
                      'search_query': search_query,
                      'sort':sort,
                      'page_obj': page_obj
                  })

def product_details(request, variant_id):
    # First check if variant exists
    try:
        variant = ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return redirect('shop')

    # Then check if it is active
    if variant.status != 'active' or variant.product.status != 'active' or variant.product.category.status != 'active':
        return redirect('shop')

    other_variants = ProductVariant.objects.filter(
        product=variant.product,
        status='active',
        product__status='active',
        product__category__status='active'
    )

    related_variants = ProductVariant.objects.filter(
        product__category = variant.product.category,
        product__category__status='active',
        product__status = 'active',
        status = 'active'
    ).exclude(product=variant.product)[:4]

    return render(request, 'user/product_details.html', {
        'variant': variant,
        'other_variants': other_variants,
        'related_variants': related_variants
    })

def collections(request):
    categories = Category.objects.filter(status='active')
    return render(request,'user/collections.html',{
        'categories':categories
    })

def collection_details(request,category_id):

    try:
        category = Category.objects.get(id=category_id, status='active')
    except Category.DoesNotExist:
        return redirect('collections')

    variants = ProductVariant.objects.filter(
        product__category = category,
        product__status = 'active',
        product__category__status = 'active',
        status = 'active'
    )

    search_query = request.GET.get('search', '')
    selected_price = request.GET.get('price', '')
    sort = request.GET.get('sort', '')

    # Search
    if search_query:
        variants = variants.filter(product__product_name__icontains=search_query)

    # Price filter
    if selected_price == 'under_3000':
        variants = variants.filter(price__lt=3000)
    elif selected_price == '3000_5000':
        variants = variants.filter(price__gte=3000, price__lte=5000)
    elif selected_price == '5000_8000':
        variants = variants.filter(price__gte=5000, price__lte=8000)
    elif selected_price == 'above_8000':
        variants = variants.filter(price__gt=8000)

    # Sort
    if sort == 'price_low':
        variants = variants.order_by('price')
    elif sort == 'price_high':
        variants = variants.order_by('-price')
    elif sort == 'a_z':
        variants = variants.order_by('product__product_name')
    elif sort == 'z_a':
        variants = variants.order_by('-product__product_name')

    return render(request, 'user/collection_details.html', {
        'category': category,
        'variants': variants,
        'search_query': search_query,
        'selected_price': selected_price,
        'sort': sort
    })

@login_required
def cart(request):
    # get the cart for this user
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)

    # get all items in that cart
    items = CartItem.objects.filter(cart=cart)

    subtotal = sum(item.total_price for item in items)

    return render(request, 'user/cart_page.html', {
        'cart': cart,
        'items': items,
        'subtotal': subtotal
    })

@login_required
def add_to_cart(request, variant_id):
    if request.method == 'POST':

        # get the variant from DB        
        variant = get_object_or_404(ProductVariant, id=variant_id, status='active')

        # get the cart for this user
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=request.user)

        # check if this variant is already in the cart
        try:
            item = CartItem.objects.get(cart=cart, product_variant=variant)

            # item already exists
            # check max quantity limit
            if item.quantity >= 5:
                messages.error(request, "Maximum 5 items allowed per product!")
                return redirect('product_details', variant.id)

            # check stock availability
            if item.quantity + 1 > variant.stock:
                messages.error(request, "Not enough stock available!")
                return redirect('product_details', variant.id)

            # all good - increase quantity by 1
            item.quantity = item.quantity + 1
            item.total_price = variant.price * item.quantity
            item.save()

        except CartItem.DoesNotExist:

            # item not in cart yet, create a new cart item
            item = CartItem.objects.create(
                cart=cart,
                product_variant=variant,
                quantity=1,
                total_price=variant.price
            )

        messages.success(request, f"{variant.product.product_name} added to cart!")        
        return redirect('product_details', variant.id)

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':

        # get the cart item
        # if not found, return 404
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            messages.error(request, "Item not found in cart!")
            return redirect('cart')

        item.delete()

        messages.success(request, "Item removed from cart!")

        return redirect('cart')

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':

        # get the cart item
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            messages.error(request, "Item not found in cart!")
            return redirect('cart')

        # get the quantity from the form
        quantity = int(request.POST.get('quantity'))

        if quantity > 5:
            messages.error(request, "Maximum 5 items allowed per product!")
            return redirect('cart')

        # if quantity is 0 or less, remove the item
        if quantity < 1:
            item.delete()
            messages.success(request, "Item removed from cart!")
            return redirect('cart')

        # check if requested quantity is available in stock
        if quantity > item.product_variant.stock:
            messages.error(request, "Not enough stock!")
            return redirect('cart')

        # pdate quantity and total price
        item.quantity = quantity
        item.total_price = item.product_variant.price * quantity
        item.save()

        # redirect back to cart page
        return redirect('cart')