from django import forms

from .models import Post, Comment, User


class BlogForm(forms.ModelForm):

    class Meta:
        model = Post
        # fields = '__all__'
        exclude = ('author',)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        # fields = '__all__'
        # exclude = ('post',)


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name',
                  'last_name',
                  'username',
                  'email')
