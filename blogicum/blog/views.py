from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.http.request import HttpRequest as HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    ListView, DeleteView, CreateView, UpdateView, DetailView
)

from .models import Post, Category, User, Comment
from .forms import BlogForm, CommentForm, ProfileForm


POSTS_IN_PAGE = 10


def get_post_object(filter=False, annotate_sort=False):
    post_query = Post.objects.select_related(
        'author',
        'category'
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
            raise Http404("You do not have permission to edit this post.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})


class PostsDetailView(DetailView):
    """Объект для отображения определенного поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post_id = self.kwargs.get('post_id')
        get_posts = get_post_object()
        post = get_object_or_404(get_posts, pk=post_id)
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
    ordering = 'post__pub_date'
    context_object_name = 'post'

    def get_object_category_by_slug(self, slug):
        return get_object_or_404(Category, slug=slug, is_published=True)

    def get_queryset(self):
        category_slug = self.kwargs.get('category')
        self.get_object_category_by_slug(category_slug)
        return get_post_object(filter=True, annotate_sort=True).filter(
            category__slug=category_slug)

    def get_context_data(self, **kwargs):
        category_slug = self.kwargs.get('category')
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_object_category_by_slug(category_slug)
        return context


class CommentMixin:
    model = Comment

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        post_id = self.kwargs.get('post_id')
        comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
        return comment

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=comment.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id':
                                                   self.object.post.pk})


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
        return reverse('blog:post_detail', kwargs={'post_id':
                                                   self.kwargs['post_id']})


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    """Объект для редактирования комментариев."""

    template_name = 'blog/comment.html'
    form_class = CommentForm
    pk_url_kwarg = 'post_id'


class CommentDeleteView(CommentMixin, LoginRequiredMixin, DeleteView):
    """Объект для удаления комментариев."""

    model = Comment
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
        if self.request.user.username != self.get_object().username:
            query = get_post_object(filter=True, annotate_sort=True)
        else:
            query = get_post_object(annotate_sort=True)
        query = query.filter(author_id=self.get_object()).order_by('-pub_date')
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
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
        return reverse('blog:profile', kwargs={'username':
                                               self.request.user.username})
