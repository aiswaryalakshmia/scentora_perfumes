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
    products = Product.objects.order_by("-created_at")

    return render(request,
        'admin/product_management.html',
        {
            'products':products
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

        return redirect('product_details', product_id=product.id)

    return render(request, 'admin/add_product.html', {
        'categories': categories
    })

def product_details(request, product_id):

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

            return redirect(
                'product_details',
                product_id=product.id
            )

    else:
        form = ProductVariantForm()

    variants = ProductVariant.objects.filter(
        product=product
    )

    return render(
        request,
        'admin/product_details.html',
        {
            'product': product,
            'form': form,
            'variants': variants
        }
    )
