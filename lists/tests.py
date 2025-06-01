import html
from urllib import request
from django.http import HttpRequest
from django.test import TestCase
from django.urls import resolve
from lists.views import home_page
from lists.models import Item, List

class NewItemTest(TestCase):

    def test_can_save_a_POST_request_to_an_existing_list(self):
        list_ = List.objects.create()
        response = self.client.post(f'/lists/{list_.id}/new_item', data={'item_text': 'A new item for an existing list'})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, list_)

    def test_redirects_to_list_view(self):
        list_ = List.objects.create()
        response = self.client.post(f'/lists/{list_.id}/new_item', data={'item_text': 'A new item for an existing list'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], f'/lists/{list_.id}/')

class ListAndItemModelTest(TestCase):
    def test_saving_and_retrieving_items(self):
        list_ = List()
        list_.save()

        first_item = Item()
        first_item.text = 'The first item'
        first_item.list = list_
        first_item.save()

        second_item = Item()
        second_item.text = 'The second item'
        second_item.list = list_
        second_item.save()

        saved_list = List.objects.first()
        self.assertEqual(saved_list, list_)

        saved_items = Item.objects.filter(list=list_)
        self.assertEqual(saved_items.count(), 2)

        self.assertEqual(saved_items[0].text, 'The first item')
        self.assertEqual(saved_items[0].list, list_)
        self.assertEqual(saved_items[1].text, 'The second item')
        self.assertEqual(saved_items[1].list, list_)


class HomePageTest(TestCase):
    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')


class ListViewTest(TestCase):
    def test_uses_list_template(self):
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertTemplateUsed(response, 'list.html')

    def test_displays_only_items_for_that_list(self):
        list1 = List.objects.create()
        Item.objects.create(text='Item 1', list=list1)
        Item.objects.create(text='Item 2', list=list1)

        list2 = List.objects.create()
        Item.objects.create(text='Item A', list=list2)
        Item.objects.create(text='Item B', list=list2)

        response = self.client.get(f'/lists/{list1.id}/')

        self.assertContains(response, 'Item 1')
        self.assertContains(response, 'Item 2')
        self.assertNotContains(response, 'Item A')
        self.assertNotContains(response, 'Item B')

    def test_passes_correct_list_to_template(self):
        list_ = List.objects.create()
        Item.objects.create(text='Item 1', list=list_)

        response = self.client.get(f'/lists/{list_.id}/')
        self.assertEqual(response.context['list'], list_)



    def test_can_save_a_POST_request(self):
        response = self.client.post('/lists/new', data={'item_text': 'A new list item'})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_redirects_after_POST(self):
        response = self.client.post('/lists/new', data={'item_text': 'A new list item'})
        self.assertEqual(response.status_code, 302)
        new_list = List.objects.first()
        self.assertEqual(response['location'], f'/lists/{new_list.id}/')
