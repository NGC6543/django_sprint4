from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.http.request import HttpRequest as HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import (
    ListView, DeleteView, CreateView, UpdateView, DetailView
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required

from .models import Post, Category, User, Comment
from .forms import BlogForm, CommentForm, ProfileForm


NUMBER_OF_POSTS = 5
POSTS_IN_PAGE = 10


class BlogCreateView(CreateView):
    '''Создание постов'''
    model = Post
    form_class = BlogForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    context_object_name = 'post'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs: reverse_lazy):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class BlogListView(ListView):
    '''Отвечает за пейджинг'''
    model = Post
    ordering = 'id'
    paginate_by = POSTS_IN_PAGE
    template_name = 'blog/index.html'


class BlogUpdateView(UpdateView):
    model = Post
    form_class = BlogForm
    template_name = 'blog/create.html'

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class BlogDeleteView(DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class BlogDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    # def get_object(self) -> Model:
    #     return super().get_object(queryset)

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
    model = Category
    template_name = 'blog/category.html'
    paginate_by = POSTS_IN_PAGE
    ordering = 'id'
    context_object_name = 'post'

    # def get_queryset(self):
    #     category_slug = self.kwargs.get('category')
    #     return Post.objects.filter(category__slug=category_slug)

    # def get(self, request: HttpRequest, *args: reverse_lazy, **kwargs: reverse_lazy) -> HttpResponse:
    #     return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: reverse_lazy):
        category_slug = self.kwargs.get('category')
        context = super().get_context_data(**kwargs)

        context['category'] = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
        )
        context['post'] = Post.objects.all()
        return context


# КОММЕНТАРИИ
class CommentMixin:
    model = Comment

class CommentCreateView(CommentMixin, CreateView):
    '''Создание комментариев?'''
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.comment = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.comment
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.comment.pk})


class CommentUpdateView(CommentMixin, UpdateView):
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})


class CommentDeleteView(CommentMixin, DeleteView):
    template_name = 'blog/comment.html'

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def get_success_url(self) -> str:
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})


class CommentDetailView(CommentMixin, DetailView):
    ...


@login_required
def add_comment(request, pk):
    # Получаем объект дня рождения или выбрасываем 404 ошибку.
    post = get_object_or_404(Post, pk=pk)
    # Функция должна обрабатывать только POST-запросы.
    form = CommentForm(request.POST)
    if form.is_valid():
        # Создаём объект поздравления, но не сохраняем его в БД.
        comment = form.save(commit=False)
        # В поле author передаём объект автора поздравления.
        comment.author = request.user
        # В поле birthday передаём объект дня рождения.
        comment.post = post
        # Сохраняем объект в БД.
        comment.save()
    # Перенаправляем пользователя назад, на страницу дня рождения.
    return redirect('blog:detail', pk=pk)


# ПРОФАЙЛ
class UserProfileMixin:
    model = User


class ProfileDetailView(UserProfileMixin, DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_url_kwarg = 'username'

    def get_object(self) -> Model:
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # self.object???
        get_posts = Post.objects.select_related('author').filter(
            author=self.object).order_by('id')
        paginator = Paginator(get_posts, POSTS_IN_PAGE).get_page(
            self.request.GET.get('page'))
        context['page_obj'] = paginator
        # context['post'] = Post.objects.select_related('category').filter(category__slug=self.request.user)

        return context


class ProfileUpdateView(UserProfileMixin, UpdateView):
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
