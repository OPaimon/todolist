from django.shortcuts import redirect, render

from lists.models import Item


def home_page(request):
    return render(request, 'home.html')

def view_list(request):
    items = Item.objects.all()
    return render(request, 'list.html', {'items': items})

def new_list(request):
    if request.method == 'POST':
        new_item_text = request.POST.get('item_text', '')
        if new_item_text:
            Item.objects.create(text=new_item_text)
        return redirect('/lists/the-new-page/')