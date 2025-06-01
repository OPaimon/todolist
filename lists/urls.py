from django.urls import path, re_path
from lists import views


urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),  # Include the URLs from the lists app
    path('new', views.new_list, name='new_list'),
    re_path(r'^(?P<list_id>\d+)/$', views.view_list, name='view_list'),
    re_path(r'^(?P<list_id>\d+)/new_item$', views.new_item, name='add_item'),
]
