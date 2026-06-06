from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category,Product, ProductVariant
from .forms import CategoryForm,ProductForm, ProductVariantForm

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
    print(list(categories))

    if request.method == "POST":
        product = Product.objects.create(
            product_name=request.POST['product_name'],
            description=request.POST['description'],
            category_id=request.POST['category']
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
            
            if "add_product_variant" in request.POST: # go to edit prodct page after adding variant from edit product page
                return redirect(
                    'edit_product',
                    product_id=product.id
                )

            return redirect( # go to add variant page after adding variant from add variant page
                'add_variant',
                product_id=product.id
            )

    else:
        form = ProductVariantForm()

    variants = ProductVariant.objects.filter(
        product=product
    )

    return render(
        request,
        'admin/add_variant.html',
        {
            'product': product,
            'form': form,
            'variants': variants
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
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == "POST":
        variant.size = request.POST.get("size")
        variant.price = request.POST.get("price")
        variant.stock = request.POST.get("stock")

        if request.FILES.get("image"):
            variant.image = request.FILES["image"]

        variant.save()

    return redirect('edit_product', product_id=variant.product.id)

def toggle_product_status(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if product.status == "active":
        product.status = "blocked"
    else:
        product.status = "active"

    product.save()

    return redirect('product_management')

def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    product_id = variant.product.id  # to redirect back
    variant.delete()

    return redirect('edit_product', product_id=product_id)
