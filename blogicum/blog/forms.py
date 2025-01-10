from django import forms

from .models import Post, Comment, User


class BlogForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={
                    'type': 'date',
                    }
                )
            }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name',
                  'last_name',
                  'username',
                  'email')
