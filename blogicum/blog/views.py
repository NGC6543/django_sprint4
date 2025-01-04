from django.db.models import Q
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import (
    ListView, DeleteView, CreateView, UpdateView, DetailView
)
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required

from .models import Post, Category, User, Comment
from .forms import BlogForm, CommentForm


NUMBER_OF_POSTS = 5
PAGINATE_PAGE = 10


class BlogCreateView(CreateView):
    '''Создание постов?'''
    model = Post
    form_class = BlogForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:profile')


# def create_post(request):
#     tempalte = 'blog/create.html'
#     return render(request, tempalte)


class BlogListView(ListView):
    '''Отвечает за пейджинг'''
    model = Post
    ordering = 'id'
    paginate_by = PAGINATE_PAGE
    template_name = 'blog/index.html'


class BlogUpdateView(UpdateView):
    model = Post


class BlogDeleteView(DeleteView):
    model = Post


class BlogDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Записываем в переменную form пустой объект формы.
        context['form'] = CommentForm()
        # context['form'] = BlogForm()
        # Запрашиваем все поздравления для выбранного дня рождения.
        print(dir(self.object))
        # context['comments'] = self.object.posts.select_related('author')
        # print('MISTAKE?')

        context['comments'] = self.object.comments.all()
        # context['post'] = Post.objects.all()
        # context['comments'] = (
        #     # Дополнительно подгружаем авторов комментариев,
        #     # чтобы избежать множества запросов к БД.
        #     self.object.comment.select_related('author')
        # )
        return context


# КОММЕНТАРИИ
class CommentCreateView(CreateView):
    '''Создание комментариев?'''
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(dir(self))
        context['form'] = CommentForm()
        print(dir(self.object))
        # context['comments'] = self.object.posts.select_related('author')
        context['comments'] = self.object.posts.all()
        return context


class CommentUpdateView(UpdateView):
    model = Comment


class CommentDeleteView(DeleteView):
    model = Comment


class CommentDetailView(DetailView):
    model = Comment


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


class UserProfileMixin:
    model = User


# ПРОФАЙЛ
class ProfileDetailView(UserProfileMixin, DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None) -> Model:
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)
        # return super().get_object(queryset)


class ProfileUpdateView(UserProfileMixin, UpdateView):
    pass


class ProfileDeleteView(UserProfileMixin, DeleteView):
    pass


def profile_detail(request, username):
    template = 'blog/profile.html'
    profile_list = Post.objects.select_related(
        'author',
    ).filter(Q(author__username=username))
    # profile_list = User.objects.all()
    # context = {'profile': profile_list}
    context = {'profile': User.objects.values()} # Использовав это выходит Регистрация
    return render(request, template, context)




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
