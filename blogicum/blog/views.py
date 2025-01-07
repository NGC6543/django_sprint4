from django.core.paginator import Paginator
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


POSTS_IN_PAGE = 10


class PostMixin:
    '''Объект для наследования модели Post.'''
    model = Post


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    '''Объект для создание постов.'''
    form_class = BlogForm
    template_name = 'blog/create.html'
    context_object_name = 'post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostListView(PostMixin, ListView):
    '''Объект для отображения постов на главной странице.'''
    queryset = Post.objects.select_related(
        'author',
        'category'
    ).annotate(comment_count=Count('comments')).filter(
        pub_date__lt=timezone.now(),
        is_published=True,
        category__is_published=True
    )
    paginate_by = POSTS_IN_PAGE
    ordering = '-pub_date'
    template_name = 'blog/index.html'


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):
    '''Объект для обновление постов.'''
    form_class = BlogForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        post_id = self.kwargs.get('pk')
        if form.instance.author != self.request.user:
            return redirect('blog:post_detail', pk=post_id)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')
        post_id = self.kwargs.get('pk')
        get_post = get_object_or_404(Post, pk=post_id)
        if get_post.author != self.request.user:
            return redirect('blog:post_detail', pk=post_id)
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    '''Объект для удаления постов.'''
    template_name = 'blog/create.html'

    def get_object(self):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_id)
        if post.author != self.request.user and not self.request.user.is_staff:
            raise Http404("You do not have permission to edit this post.")
        return post

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostsDetailView(PostMixin, DetailView):
    '''Объект для отображения определенного поста.'''
    template_name = 'blog/detail.html'

    def get_object(self):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_id)
        if (not post.is_published and post.author != self.request.user
                and not self.request.user.is_staff):
            raise Http404('You do not have permission to view this post.')
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryListView(ListView):
    '''Объект для отображения категорий.'''
    model = Category
    template_name = 'blog/category.html'
    paginate_by = POSTS_IN_PAGE
    ordering = 'post__pub_date'
    context_object_name = 'post'

    def get_queryset(self):
        category_slug = self.kwargs.get('category')
        return Post.objects.select_related('category').filter(
            category__slug=category_slug,
            pub_date__lt=timezone.now(),
            is_published=True
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        category_slug = self.kwargs.get('category')
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        return context


class CommentMixin:
    '''Объект для наследования модели Comment.'''
    model = Comment


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    '''Объект для создания комментариев.'''
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.get_post = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.get_post.pk})


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    '''Объект для редактирования комментариев.'''
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author != self.request.user and not self.request.user.is_staff:
            raise Http404('You do not have permission to edit this comment.')
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    '''Объект для удаления комментариев.'''
    template_name = 'blog/comment.html'

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        comment = get_object_or_404(Comment, pk=comment_id)
        if self.request.user != comment.author:
            raise Http404('You do not have permission to delete this comment.')
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})


class UserProfileMixin:
    '''Объект для наследования модели User.'''
    model = User


class ProfileDetailView(UserProfileMixin, DetailView, LoginRequiredMixin):
    '''Объект отображения профиля пользователя.'''
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_url_kwarg = 'username'

    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        get_posts = Post.objects.select_related('author').filter(
            author=self.object).annotate(comment_count=Count('comments')).order_by('-pub_date')
        paginator = Paginator(get_posts, POSTS_IN_PAGE).get_page(
            self.request.GET.get('page'))
        context['page_obj'] = paginator
        return context


class ProfileUpdateView(LoginRequiredMixin, UserProfileMixin, UpdateView):
    '''Объект для редактирования профиля пользователя.'''
    template_name = 'blog/user.html'
    form_class = ProfileForm
    slug_url_kwarg = 'username'

    def get_object(self):
        return self.request.user

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user.username})
