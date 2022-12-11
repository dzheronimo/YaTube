from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (ListView, DetailView,
                                  FormView, CreateView, UpdateView, View)
from django.urls import reverse
from .models import Group, Post, User, Comment, Follow
from .forms import PostForm, CommentForm


POSTS_PER_PAGE = 10


class IndexListView(ListView):
    model = Post
    template_name = 'posts/index.html'
    paginate_by = POSTS_PER_PAGE


class GroupListView(ListView):
    template_name = 'posts/group_list.html'
    paginate_by = POSTS_PER_PAGE

    def get_object(self):
        group = get_object_or_404(Group, slug=self.kwargs.get('slug'))
        return group

    def get_queryset(self):
        group = self.get_object()
        self.queryset = group.posts
        return self.queryset.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.get_object()
        return context


class ProfileListView(ListView):
    template_name = 'posts/profile.html'
    paginate_by = POSTS_PER_PAGE

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return user

    def get_queryset(self):
        user = self.get_object()
        self.queryset = user.posts
        return self.queryset.all()

    def get_context_data(self, **kwargs):
        author = self.get_object()
        context = super().get_context_data(**kwargs)
        context['author'] = author
        if self.request.user.is_authenticated:
            context['following'] = self.request.user.follower.filter(
                author__username=author.username)

        return context


class PostDetailView(DetailView, FormView):
    model = Post
    context_object_name = 'post'
    template_name = 'posts/post_detail.html'
    pk_url_kwarg = 'post_id'
    form_class = CommentForm
    symbols_count = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['post']
        title = f'Пост {post.text[:self.symbols_count]}'
        author_fullname = f'{post.author.first_name} {post.author.last_name}'
        context['comments'] = post.comments.all()
        context['title'] = title
        context['author_fullname'] = author_fullname
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'
    extra_context = {'is_edit': False}

    def form_valid(self, form):
        user = self.request.user
        post = form.save(commit=False)
        post.author = user
        form.save()
        return redirect('posts:profile', user.username)


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(Post, id=self.kwargs.get('post_id'))
        return obj

    def get(self, request, *args, **kwargs):
        post = self.get_object()
        if not request.user == post.author:
            return redirect('posts:post_detail', post.id)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        if not request.user == post.author:
            return redirect('posts:post_detail', post.id)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = get_object_or_404(Post, id=self.kwargs.get('post_id'))
        context['author'] = author
        context['is_edit']: True
        return context


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def get_object(self, queryset=None):
        obj = Post.objects.get(id=self.kwargs.get('post_id'))
        return obj

    def form_valid(self, form):
        post = self.get_object()
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = post
        form.save()
        return redirect('posts:post_detail', post.id)


class FollowIndexView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/follow.html'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        user = self.request.user
        post_list_follow = Post.objects.filter(
            author__following__user=user
        )
        self.queryset = post_list_follow
        return self.queryset


class ProfileFollow(LoginRequiredMixin, View):
    model = Follow

    def get(self, request, **kwargs):
        author_username = kwargs.get('username')
        author = User.objects.get(username=author_username)
        follower = request.user.follower.filter(
            author__username=author_username)
        if author.id != request.user.id and not follower.exists():
            Follow.objects.create(
                user=request.user,
                author=author
            )
        return redirect(
            reverse(
                'posts:profile',
                kwargs={'username': self.kwargs.get('username')})
        )


class ProfileUnfollow(LoginRequiredMixin, View):
    model = Follow

    def get(self, request, **kwargs):
        author_username = kwargs.get('username')
        author = User.objects.get(username=author_username)
        followings = request.user.follower.filter(
            author__username=author_username)
        if author.id != request.user.id:
            if followings.exists():
                followings.delete()
        return redirect(
            reverse(
                'posts:profile',
                kwargs={'username': self.kwargs.get('username')})
        )
