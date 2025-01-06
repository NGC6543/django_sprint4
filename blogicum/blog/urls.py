from django.urls import path

from . import views


app_name = 'blog'

urlpatterns = [
    path('', views.BlogListView.as_view(), name='index'),
    # path('posts/<int:id>/', views.post_detail, name='post_detail'),
    path('posts/<int:pk>/', views.BlogDetailView.as_view(), name='post_detail'),
    # path('category/<slug:category>/', views.category_posts,
    #      name='category_posts'),
    path('category/<slug:category>/', views.CategoryListView.as_view(),
         name='category_posts'),
    path('posts/create/', views.BlogCreateView.as_view(), name='create_post'),
    # path('posts/<int:id>/create/', views.create_post, name='create_post'),
    path('posts/<int:pk>/edit/', views.BlogUpdateView.as_view(), name='edit_post'),
    path('posts/<int:pk>/delete/', views.BlogDeleteView.as_view(), name='delete_post'),
    path('posts/<int:pk>/comment/', views.CommentCreateView.as_view(), name='add_comment'),
    path('posts/<int:pk>/edit_comment/<int:comment_id>/', views.CommentUpdateView.as_view(), name='edit_comment'),
    path('posts/<int:pk>/delete_comment/<int:comment_id>/', views.CommentDeleteView.as_view(), name='delete_comment'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/<slug:username>/', views.ProfileDetailView.as_view(), name='profile'),
]
# urlpatterns = [
#     path('', views.index, name='index'),
#     path('posts/<int:id>/', views.post_detail, name='post_detail'),
#     path('category/<slug:category>/', views.category_posts,
#          name='category_posts'),
#     path('profile/', views.profile_detail, name='profile')
# ]
