from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Address

@login_required
def profile_dashboard(request):
    user=request.user

    context = {   
        'current_user':user,
        'total_orders': 0,
        'wishlist_count': 0,
        'wallet_balance': 0,
        'pending_orders': 0,
    }
    
    return render(request,'userprofile.html',context)
    
@login_required   
def address_book(request):
     addresses=Address.objects.filter(user=request.user)

     context={
          'addresses':addresses
     }

     return render(request,'address_book.html',context)

@login_required
def add_address(request):
    if request.method == 'POST':
        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
              user=request.user,
              full_name=request.POST.get('full_name'),
              phone_number=request.POST.get('phone_number'),
              address_line1=request.POST.get('address_line1'),
              address_line2=request.POST.get('address_line2'),
              city=request.POST.get('city'),
              state=request.POST.get('state'),
              country=request.POST.get('country'),
              pincode=request.POST.get('pincode'),
              address_type=request.POST.get('address_type'),
              is_default=True if request.POST.get('is_default') else False
        )
        return redirect('address_book')
    return render(request,'add_address.html')

@login_required
def delete_address(request,address_id):
    address=get_object_or_404(
        Address,
        user=request.user,
        id=address_id
    )

    address.delete()

    return redirect('address_book')

@login_required
def edit_address(request,address_id):
    try:
        address=Address.objects.get(
            id=address_id,
            user=request.user
            )
    except Address.DoesNotExist:
        return redirect('address_book')    
    
    if request.method=='POST':

        if request.POST.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)

        address.full_name = request.POST.get('full_name')
        address.phone_number = request.POST.get('phone_number')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        address.pincode = request.POST.get('pincode')
        address.address_type = request.POST.get('address_type')
        address.is_default=True if request.POST.get('is_default') else False

        
        address.save()
        return redirect('address_book')
    return render(request,'add_address.html',
                  {'address':address})