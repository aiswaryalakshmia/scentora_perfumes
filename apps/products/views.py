from django.shortcuts import render,redirect
from .models import Category
from .forms import CategoryForm

def category_management(request):
    categories = Category.objects.all()
    return render(
        request,
        'admin/category_management.html',
        {
            'categories': categories
        }
    )

def add_category(request):

    # If user submitted form
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # check if data is valid
        if form.is_valid():
            form.save()   # SAVE TO DATABASE
            return redirect('category_management')

    # If user just opened page
    else:
        form = CategoryForm()

    return render(request, 'admin/add_category.html', {'form': form})
