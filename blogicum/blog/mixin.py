from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import Comment


class CommentMixin:
    """Миксин для объектов редактирования и удаления комментариев."""

    model = Comment

    def get_object(self):
        return get_object_or_404(Comment,
                   pk=self.kwargs.get('comment_id'),
                   post_id=self.kwargs.get('post_id'))

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
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs.get('post_id')})
