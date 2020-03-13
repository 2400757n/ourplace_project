
from django.urls import path
from ourplace import views

app_name = 'ourplace'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('canvas/<str:canvas_name_slug>/', views.show_canvas, name='show_canvas'),
    path('faq/', views.faq, name='faq'),
    path('login/', views.login, name='login'),
    path('account/', views.account, name='account'),
    path('user/{username}/', views.user, name='user'),
    path('place/', views.create_place, name='create_place'),
    path('place/{place_name}/', views.view_place, name='view_place'),
    path('search/', views.search, name='search')
]