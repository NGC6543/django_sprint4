from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    ListView, DeleteView, CreateView, UpdateView, DetailView
)

from .models import Post, Category, User, Comment
from .forms import BlogForm, CommentForm, ProfileForm
from .mixin import CommentMixin


POSTS_IN_PAGE = 10


def get_post_object(filter=False, annotate_sort=False):
    """Функция для получения данных модели Post.
    Данные можно получить дополнительно их отфильтровав
    или добавив счётчик комментариев и сортировку.
    """
    post_query = Post.objects.select_related(
        'author',
        'category',
        'location'
    )
    if filter:
        post_query = post_query.filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True
        )
    if annotate_sort:
        post_query = post_query.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return post_query


class PostCreateView(LoginRequiredMixin, CreateView):
    """Объект для создание постов."""

    model = Post
    form_class = BlogForm
    template_name = 'blog/create.html'
    context_object_name = 'post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class PostListView(ListView):
    """Объект для отображения постов на главной странице."""

    queryset = get_post_object(filter=True, annotate_sort=True)
    paginate_by = POSTS_IN_PAGE
    template_name = 'blog/index.html'


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Объект для обновление постов."""

    model = Post
    form_class = BlogForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        get_post = self.get_object()
        if get_post.author != self.request.user:
            return redirect('blog:post_detail', post_id=get_post.pk)
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Объект для удаления постов."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class PostsDetailView(DetailView):
    """Объект для отображения определенного поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post = get_object_or_404(get_post_object(), pk=self.kwargs['post_id'])
        if (post.author != self.request.user
                and (not post.is_published or not post.category.is_published
                     or post.pub_date > timezone.now())):
            raise Http404('You do not have permission to view this post.')
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryListView(ListView):
    """Объект для отображения категорий."""

    template_name = 'blog/category.html'
    paginate_by = POSTS_IN_PAGE
    context_object_name = 'post'

    def get_object_category_by_slug(self):
        """Метод для получения категории"""
        return get_object_or_404(Category, slug=self.kwargs['category'],
                                 is_published=True)

    def get_queryset(self):
        get_category = self.get_object_category_by_slug()
        return get_post_object(filter=True, annotate_sort=True).filter(
            category=get_category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_object_category_by_slug()
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Объект для создания комментариев."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    """Объект для редактирования комментариев."""

    template_name = 'blog/comment.html'
    form_class = CommentForm
    pk_url_kwarg = 'post_id'


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    """Объект для удаления комментариев."""

    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'


class ProfileListView(ListView):
    """Объект отображения профиля пользователя."""

    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_url_kwarg = 'username'
    paginate_by = POSTS_IN_PAGE

    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_queryset(self):
        user_object = self.get_object()
        return get_post_object(filter=self.request.user != user_object,
                               annotate_sort=True).filter(
                                   author=user_object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Объект для редактирования профиля пользователя."""

    model = User
    template_name = 'blog/user.html'
    form_class = ProfileForm
    slug_url_kwarg = 'username'

    def get_object(self):
        return self.request.user

    def get_success_url(self) -> str:
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})
