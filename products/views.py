from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product
from .forms import ProductForm

@login_required
def product_list(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "products/product_list.html", {"products": products})

@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product/Service added successfully")
            return redirect("products:product_list")
    else:
        form = ProductForm()
    return render(request, "products/product_form.html", {"form": form})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product/Service updated successfully")
            return redirect("products:product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "products/product_form.html", {"form": form, "edit": True})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product/Service deleted successfully")
        return redirect("products:product_list")
    return render(request, "products/product_confirm_delete.html", {"product": product})
