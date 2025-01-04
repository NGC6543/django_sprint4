from django import forms

from .models import Post, Comment


class BlogForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = '__all__'


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        # fields = '__all__'
        # exclude = ('post',)
