from typing import Any
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.http.request import HttpRequest as HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import (
    ListView, DeleteView, CreateView, UpdateView, DetailView
)
from django.urls import reverse

from .models import Post, Category, User, Comment
from .forms import BlogForm, CommentForm, ProfileForm


from django.http import Http404

NUMBER_OF_POSTS = 5
POSTS_IN_PAGE = 10


class PostMixin:
    '''Объект для наследования модели Post'''
    model = Post


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    '''Объект для создание постов'''
    form_class = BlogForm
    template_name = 'blog/create.html'
    context_object_name = 'post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostListView(PostMixin, ListView):
    '''Объект для отображения постов на главной странице'''
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
    '''Объект для обновление постов'''
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
        post = get_object_or_404(Post, pk=post_id)
        if post.author != self.request.user:
            return redirect('blog:post_detail', pk=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_id)
        if post.author != self.request.user and not self.request.user.is_staff:
            raise Http404("You do not have permission to edit this post.")
        return post

    def get_success_url(self) -> str:
        # return reverse('blog:profile', kwargs={'username': self.request.user})
        return reverse('blog:post_detail',
                       kwargs={'pk': self.kwargs.get('pk')})


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    '''Объкт для удаления постов'''
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_object(self):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_id)
        if post.author != self.request.user and not self.request.user.is_staff:
            raise Http404("You do not have permission to edit this post.")
        return post

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostsDetailView(PostMixin, DetailView):
    '''Объект для отображения определенного поста'''
    template_name = 'blog/detail.html'

    def get_object(self):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_id)
        if not post.is_published and post.author != self.request.user and not self.request.user.is_staff: 
            raise Http404("You do not have permission to view this post.") 
        return post
        # if post.author != self.request.user:
        #     raise Http404("You do not have permission to edit this post.")
        # return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        # context['comments'] = (
        #     # Дополнительно подгружаем авторов комментариев,
        #     # чтобы избежать множества запросов к БД.
        #     self.object.comment.select_related('author')
        # )
        return context


class CategoryListView(ListView):
    '''Объект для отображения категорий'''
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
        # context['post'] = Post.objects.all()
        context['post'] = Post.objects.prefetch_related('category')
        return context


class CommentMixin:
    '''Объект для наследования модели Comment'''
    model = Comment


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    '''Объект для создания комментариев'''
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.get_post = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.get_post.pk})


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):
    '''Объект для редактирования комментариев'''
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author != self.request.user and not self.request.user.is_staff:
            raise Http404("You do not have permission to edit this comment.")
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    '''Объект для удаления комментариев'''
    template_name = 'blog/comment.html'

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        comment = get_object_or_404(Comment, pk=comment_id)
        if self.request.user != comment.author:
            raise Http404('You can\'t edit this comment')
        return comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})


class UserProfileMixin:
    '''Объект для наследования модели User'''
    model = User


class ProfileDetailView(UserProfileMixin, DetailView, LoginRequiredMixin):
    '''Объект отображения профиля пользователя'''
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_url_kwarg = 'username'

    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # self.object???
        # if self.request.user == self.object:
        #     get_posts = Post.objects.filter(author=self.object).select_related('author').annotate(comment_count=Count('comments')).order_by('-pub_date') 
        # else:
        #     get_posts = Post.objects.filter(author=self.get_object(), is_published=True).annotate(comment_count=Count('comments')).order_by('-pub_date') 
        # paginator = Paginator(get_posts, POSTS_IN_PAGE).get_page(
        #     self.request.GET.get('page'))
        # context['page_obj'] = paginator
        # return context
        # if self.request.user == self.object:
        #     get_posts = Post.objects.select_related('author').filter(
        #         author=self.object).annotate(comment_count=Count('comments')).order_by('-pub_date')
        # else:
        #     get_posts = Post.objects.select_related('author').filter(
        #         author=self.get_object(), is_published=True).annotate(comment_count=Count('comments')).order_by('-pub_date')
        get_posts = Post.objects.select_related('author').filter(
            author=self.object).annotate(comment_count=Count('comments')).order_by('-pub_date')
        paginator = Paginator(get_posts, POSTS_IN_PAGE).get_page(
            self.request.GET.get('page'))
        context['page_obj'] = paginator
        return context


class ProfileUpdateView(LoginRequiredMixin, UserProfileMixin, UpdateView):
    '''Объект для редактирования профиля пользователя'''
    template_name = 'blog/user.html'
    form_class = ProfileForm
    slug_url_kwarg = 'username'

    def get_object(self):
        return self.request.user

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


def get_selected_objects():
    """Функция возвращает объект QuerySet
    содержащий данные таблицы Post.
    """
    return Post.objects.select_related(
        'author',
        'location',
        'category').filter(
            Q(is_published=True)
            & Q(category__is_published=True)
            & Q(pub_date__lt=timezone.now())
    )


def index(request):
    template = 'blog/index.html'
    post_list_main_page = get_selected_objects()[:NUMBER_OF_POSTS]
    context = {'post_list': post_list_main_page}
    return render(request, template, context)


def post_detail(request, id):
    template = 'blog/detail.html'
    post_list_detail = get_selected_objects()
    post = get_object_or_404(post_list_detail, pk=id)
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category,
        is_published=True
    )
    post_list_category = get_selected_objects().filter(
        Q(category=category)
    )
    context = {'category': category,
               'post_list': post_list_category}
    return render(request, template, context)
