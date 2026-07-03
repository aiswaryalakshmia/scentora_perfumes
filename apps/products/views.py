import json
import base64
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.files.base import ContentFile
from apps.common.decorators import admin_required
from .models import Category,Product,ProductVariant,VariantImage,Cart,CartItem,Wishlist
from .forms import CategoryForm,ProductForm, ProductVariantForm
from .utils import get_offer_price
from .models import Offer

@admin_required
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

@admin_required
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

@admin_required
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

@admin_required
def toggle_category_status(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if category.status == 'active':
        category.status = 'inactive'

        # block all products under this category
        Product.objects.filter(category=category).update(status='inactive')

        # block all variants under this category
        ProductVariant.objects.filter(product__category=category).update(status='inactive')

        messages.success(request, f'{category.category_name} blocked successfully.')

    else:
        category.status = 'active'

        # unblock all products under this category
        Product.objects.filter(category=category).update(status='active')

        # unblock all variants under this category
        ProductVariant.objects.filter(product__category=category).update(status='active')

        messages.success(request, f'{category.category_name} unblocked successfully.')

    category.save()
    return redirect('category_management')

@admin_required
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

@admin_required
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

@admin_required
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
                return render(
                    request,
                    "admin/add_variant.html",
                    {
                        "product": product,
                        "form": form,
                        "variants": ProductVariant.objects.filter(product=product),
                    }
                )

            try:
                images = json.loads(cropped_images)

                if len(images) < 3:
                    messages.error(
                        request,
                        "Please upload at least 3 images."
                    )
                    return render(
                        request,
                        "admin/add_variant.html",
                        {
                            "product": product,
                            "form": form,
                            "variants": ProductVariant.objects.filter(product=product),
                        }
                    )

            except Exception:
                messages.error(
                    request,
                    "Invalid image data."
                )
                return render(
                    request,
                    "admin/add_variant.html",
                    {
                        "product": product,
                        "form": form,
                        "variants": ProductVariant.objects.filter(product=product),
                    }
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

@admin_required
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

@admin_required
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

@admin_required
def toggle_variant_status(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if variant.status == 'active':
        variant.status = 'inactive'
    else:
        variant.status = 'active'

    variant.save()

    return redirect('edit_product', product_id=variant.product.id)

@admin_required
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

@admin_required
def toggle_product_status(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.status == "active":
        product.status = "inactive"
        # block all variants under this product
        ProductVariant.objects.filter(product=product).update(status='inactive')
    else:
        product.status = "active"
        # unblock all variants under this product
        ProductVariant.objects.filter(product=product).update(status='active')

    product.save()
    return redirect('product_management')

@admin_required
def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    product_id = variant.product.id  # to redirect back
    variant.delete()

    messages.success(
        request,
        "Variant deleted successfully."
    )

    return redirect('edit_product', product_id=product_id)

@login_required
def shop(request):

    variants = ProductVariant.objects.filter(
        status = 'active',
        product__status = 'active',
        product__category__status = 'active'
    ).order_by('-created_at')
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

    # get all wishlisted variant ids for this user
    if request.user.is_authenticated:
        wishlisted_ids = list(Wishlist.objects.filter(
            user=request.user
        ).values_list('product_variant_id', flat=True))
    else:
        wishlisted_ids = []

    offer_price_map = {}
    for variant in page_obj:
        final_price, discount_amount, offer = get_offer_price(variant)
        offer_price_map[variant.id] = {
            'final_price':     final_price,
            'discount_amount': discount_amount,
            'offer':           offer,
            'has_offer':       offer is not None,
        }

    return render(request,'user/shop_page.html',
                  {
                      'variants':page_obj,
                      'categories':categories,
                      'selected_categories': selected_categories,
                      'selected_price': selected_price,
                      'search_query': search_query,
                      'sort':sort,
                      'page_obj': page_obj,
                      'wishlisted_ids': wishlisted_ids,
                      'offer_price_map': offer_price_map,
                  })

@login_required
def product_details(request, variant_id):
    # First check if variant exists
    try:
        variant = ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return redirect('shop')

    # Then check if it is active
    if variant.status != 'active' or variant.product.status != 'active' or variant.product.category.status != 'active':
        return redirect('shop')
    
    # for size selector dropdown
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

    is_wishlisted = Wishlist.objects.filter(user=request.user, product_variant=variant).exists()

    final_price, discount_amount, offer = get_offer_price(variant)

    # Offer prices for other size variants (size selector dropdown)
    other_variant_prices = {}
    for v in other_variants:
        fp, da, o = get_offer_price(v)
        other_variant_prices[v.id] = {
            'final_price':     fp,
            'discount_amount': da,
            'offer':           o,
        }
    return render(request, 'user/product_details.html', {
        'variant': variant,
        'other_variants': other_variants,
        'related_variants': related_variants,
        'is_wishlisted':is_wishlisted,
        'final_price': final_price,           
        'discount_amount': discount_amount,       
        'offer': offer,                 
        'other_variant_prices': other_variant_prices,  
    })

@login_required
def collections(request):
    categories = Category.objects.filter(status='active')
    return render(request,'user/collections.html',{
        'categories':categories
    })

@login_required
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

    if request.user.is_authenticated:
        wishlisted_ids = list(Wishlist.objects.filter(
            user=request.user
        ).values_list('product_variant_id', flat=True))
    else:
        wishlisted_ids = []

    return render(request, 'user/collection_details.html', {
        'category': category,
        'variants': variants,
        'search_query': search_query,
        'selected_price': selected_price,
        'sort': sort,
        'wishlisted_ids': wishlisted_ids,
    })

@login_required
def cart(request):
    # get the cart for this user
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)

    # get all items in that cart
    items = CartItem.objects.filter(cart=cart).select_related(
        'product_variant__product__category'
    ).order_by('id')

    # the stored total_price in DB is stale — this keeps it always current
    for item in items:
        final_price, _, _ = get_offer_price(item.product_variant)
        new_total = final_price * item.quantity
        if new_total != item.total_price:
            item.total_price = new_total
            item.save()

    # re-fetching ensures the calculations below use the updated values
    items = CartItem.objects.filter(cart=cart).select_related(
        'product_variant__product__category'
    ).order_by('id')

    subtotal = sum(
        item.product_variant.price * item.quantity
        for item in items
    )

    # total_discount = difference between original price and offer/discounted price
    # total_price in CartItem is already stored as offer price (from add_to_cart)
    total_discount = sum(
        (item.product_variant.price * item.quantity) - item.total_price
        for item in items
    )

    total = subtotal - total_discount
    return render(request, 'user/cart_page.html', {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'total_discount': total_discount,
        'total' : total
    })

@login_required
def add_to_cart(request, variant_id):
    if request.method == 'POST':

        # get the variant from DB        
        variant = get_object_or_404(ProductVariant, id=variant_id)

        # if not in stock or inactive redirect to product detail page
        if variant.stock == 0 or variant.status == 'inactive' or variant.product.status == 'inactive' or variant.product.category.status == 'inactive':
            if variant.status == 'inactive' or variant.product.status == 'inactive' or variant.product.category.status == 'inactive':
                messages.error(request, "Currently unavailabe!")

            next_page = request.POST.get('next', '')
            if next_page == 'product_details':
                return redirect('product_details', variant.id)
            
            elif next_page == 'shop':
                return redirect('shop')
            
            elif next_page == 'wishlist':
                return redirect('wishlist')
            
            elif next_page == 'collection_details':
                return redirect('collection_details',variant.product.category.id)
            
            else:
                return redirect('shop')
            
        #get offer price at time of adding to cart
        final_price, discount_amount, offer = get_offer_price(variant)

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

            # if all good then increase quantity by 1
            item.quantity = item.quantity + 1
            item.total_price = final_price  * item.quantity
            item.save()

        except CartItem.DoesNotExist:

            # item not in cart yet, create a new cart item
            item = CartItem.objects.create(
                cart=cart,
                product_variant=variant,
                quantity=1,
                total_price=final_price 
            )

        # remove from wishlist if it exists
        Wishlist.objects.filter(user=request.user, product_variant=variant).delete()

        messages.success(request, f"{variant.product.product_name} added to cart!")

        # redirect based on where request came from
        next_page = request.POST.get('next', '')
        if next_page == 'shop':
            return redirect('shop')

        elif next_page == 'collection_details':
            return redirect('collection_details', variant.product.category.id)

        # if request came from wishlist page, redirect back to wishlist
        elif next_page == 'wishlist':
            return redirect('wishlist')

        return redirect('product_details', variant.id)

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':

        # get the cart item        
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
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            messages.error(request, "Item not found in cart!")
            return redirect('cart')
        
        if (
            item.product_variant.stock == 0 or
            item.product_variant.status == 'inactive' or
            item.product_variant.product.status == 'inactive' or
            item.product_variant.product.category.status == 'inactive'
        ):
            item.delete()
            messages.error(request, "Item unavailable!")
            return redirect('cart')

        quantity = int(request.POST.get('quantity'))

        if quantity > 5:
            messages.error(request, "Maximum 5 items allowed per product!")
            return redirect('cart')

        if quantity < 1:
            item.delete()
            messages.success(request, "Item removed from cart!")
            return redirect('cart')

        if quantity > item.product_variant.stock:
            messages.error(request, "Not enough stock!")
            return redirect('cart')
        
        final_price, _, _ = get_offer_price(item.product_variant)
        item.quantity = quantity
        item.total_price = final_price  * quantity
        item.save()

        return redirect('cart')

@login_required
def wishlist(request):

    # get all wishlist items for this user
    wishlist_items = Wishlist.objects.filter(
        user=request.user,
        product_variant__status='active',
        product_variant__product__status='active',
        product_variant__product__category__status='active')

    return render(request, 'user/wishlist.html', {
        'wishlist_items': wishlist_items
    })

@login_required
def add_to_wishlist(request, variant_id):
    if request.method == 'POST':

        # get the variant from DB
        variant = get_object_or_404(ProductVariant, id=variant_id)
        next_page = request.POST.get('next', '')

        if variant.status == 'inactive' or variant.product.status == 'inactive' or variant.product.category.status == 'inactive':
            messages.error(request, "Currently unavailabe!")
            
            if next_page == 'product_details':
                return redirect('product_details', variant.id)
            
            elif next_page == 'shop':
                return redirect('shop')
            
            elif next_page == 'collection_details':
                return redirect('collection_details',variant.product.category.id)


        # Check first, then decide to add or remove
        existing = Wishlist.objects.filter(user=request.user, product_variant=variant).first()

        if existing:
            # Already in wishlist → remove it
            existing.delete()
            messages.success(request, f"{variant.product.product_name} removed from wishlist!")
        else:
            # Not in wishlist → add it
            Wishlist.objects.create(user=request.user, product_variant=variant)
            messages.success(request, f"{variant.product.product_name} added to wishlist!")
        
        if next_page == 'shop':
            return redirect('shop')
        elif next_page == 'collection_details':
            return redirect('collection_details', variant.product.category.id)
       
        return redirect('product_details', variant.id)

@login_required
def remove_from_wishlist(request, variant_id):
    if request.method == 'POST':
        next_page = request.POST.get('next', '')
        # get the variant from DB
        variant = get_object_or_404(ProductVariant, id=variant_id, status='active')

        # delete the wishlist item
        Wishlist.objects.filter(user=request.user, product_variant=variant).delete()
        messages.success(request, "Removed from wishlist!")
        
        if next_page == 'product_details':
            return redirect('product_details',variant.id)
        else:
            return redirect('wishlist')


@admin_required
def offer_management(request):
    offers = Offer.objects.select_related('product', 'category').order_by('-created_at')
    return render(request, 'admin/offer_management.html', {'offers': offers})


@admin_required
def add_offer(request):
    if request.method == 'POST':
        offer_type          = request.POST.get('offer_type')
        offer_name          = request.POST.get('offer_name', '').strip()
        discount_percentage = request.POST.get('discount_percentage')
        start_date          = request.POST.get('start_date')
        end_date            = request.POST.get('end_date')
        product_id          = request.POST.get('product_id')
        category_id         = request.POST.get('category_id')

        # Basic validation
        if not offer_name:
            messages.error(request, "Offer name is required.")
            return redirect('add_offer')

        if not discount_percentage or float(discount_percentage) <= 0 or float(discount_percentage) > 100:
            messages.error(request, "Discount must be between 1 and 100.")
            return redirect('add_offer')

        if start_date >= end_date:
            messages.error(request, "End date must be after start date.")
            return redirect('add_offer')

        offer = Offer(
            offer_type          = offer_type,
            offer_name          = offer_name,
            discount_percentage = discount_percentage,
            start_date          = start_date,
            end_date            = end_date,
        )

        if offer_type == 'product':
            if not product_id:
                messages.error(request, "Please select a product.")
                return redirect('add_offer')
            offer.product = get_object_or_404(Product, id=product_id)

        elif offer_type == 'category':
            if not category_id:
                messages.error(request, "Please select a category.")
                return redirect('add_offer')
            offer.category = get_object_or_404(Category, id=category_id)

        offer.save()
        messages.success(request, "Offer created successfully!")
        return redirect('offer_management')

    products   = Product.objects.filter(status='active')
    categories = Category.objects.filter(status='active')
    return render(request, 'admin/add_offer.html', {
        'products':   products,
        'categories': categories,
    })


@admin_required
def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)

    if request.method == 'POST':
        offer.offer_name          = request.POST.get('offer_name', '').strip()
        offer.discount_percentage = request.POST.get('discount_percentage')
        offer.start_date          = request.POST.get('start_date')
        offer.end_date            = request.POST.get('end_date')
        offer.save()
        messages.success(request, "Offer updated successfully!")
        return redirect('offer_management')

    products   = Product.objects.filter(status='active')
    categories = Category.objects.filter(status='active')
    return render(request, 'admin/edit_offer.html', {
        'offer':      offer,
        'products':   products,
        'categories': categories,
    })


@admin_required
def toggle_offer_status(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.status = 'inactive' if offer.status == 'active' else 'active'
    offer.save()
    messages.success(request, f"Offer {'activated' if offer.status == 'active' else 'deactivated'} successfully.")
    return redirect('offer_management')


@admin_required
def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.delete()
    messages.success(request, "Offer deleted successfully.")
    return redirect('offer_management')