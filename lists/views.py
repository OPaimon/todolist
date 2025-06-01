from django.shortcuts import redirect, render

from lists.models import Item, List


def home_page(request):
    return render(request, 'home.html')

def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    return render(request, 'list.html', {'list': list_})

def new_list(request):
    if request.method == 'POST':
        new_item_text = request.POST.get('item_text', '')
        if new_item_text:
            list_ = List.objects.create()
            Item.objects.create(text=new_item_text, list=list_)
            return redirect(f'/lists/{list_.id}/')

    
def new_item(request, list_id):
    if request.method == 'POST':
        list_ = List.objects.get(id=list_id)
        new_item_text = request.POST.get('item_text', '')
        if new_item_text:
            Item.objects.create(text=new_item_text, list=list_)
            return redirect(f'/lists/{list_.id}/')
    return redirect(f'/lists/{list_id}/')