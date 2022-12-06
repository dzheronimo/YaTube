from .models import Post, Comment
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'image', 'group')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
