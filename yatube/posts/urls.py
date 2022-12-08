from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'posts'

urlpatterns = [
    path('', views.IndexListView.as_view(), name='index'),
    path('group/<slug>/', views.GroupListView.as_view(), name='group_posts'),
    path(
        'profile/<str:username>/',
        views.ProfileListView.as_view(),
        name='profile'),
    path(
        'posts/<int:post_id>/',
        views.PostDetailView.as_view(),
        name='post_detail'),
    path('create/', views.PostCreateView.as_view(), name='post_create'),
    path(
        'posts/<post_id>/edit/',
        views.PostEditView.as_view(),
        name='post_edit'),
    path(
        'posts/<int:post_id>/comment/',
        views.AddCommentView.as_view(),
        name='add_comment'),
    path(
        'follow/', views.FollowIndexView.as_view(), name='follow_index'
    ),
    path(
        'profile/<str:username>/follow/',
        views.ProfileFollow.as_view(),
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    )
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
