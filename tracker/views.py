from django.shortcuts import render
from .forms import PurchaseForm

def homepage(request):

    purchase_form = PurchaseForm()

    context = { 'purchase_form': purchase_form}

    return render(request, 'homepage.html', context=context)
