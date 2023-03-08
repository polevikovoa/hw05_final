from django.urls import path

from . import views

from posts.views import (index, group_posts, profile,
                         post_detail, post_create, post_edit, add_comment)

app_name = 'posts'

urlpatterns = [
    path('', index, name='index'),
    path('create/', post_create, name='post_create'),
    path('posts/<int:post_id>/edit/', post_edit, name='post_edit'),
    path('group/<slug:slug>/', group_posts, name='group_list'),
    path('profile/<str:username>/', profile, name='profile'),
    path('posts/<int:post_id>/', post_detail, name='post_detail'),
    path('posts/<int:post_id>/comment/', add_comment, name='add_comment'),
    path('follow/', views.follow_index, name='follow_index'),
    path('profile/<str:username>/follow/',
         views.profile_follow,
         name='profile_follow'
         ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
