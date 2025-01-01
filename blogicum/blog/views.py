from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Post, Category


NUMBER_OF_POSTS = 5


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
