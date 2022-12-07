from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, FormView, CreateView
from django.views.generic import UpdateView
from .models import Group, Post, User, Comment, Follow
from .forms import PostForm, CommentForm


POSTS_PER_PAGE = 10


class IndexListView(ListView):
    model = Post
    template_name = 'posts/index.html'
    paginate_by = POSTS_PER_PAGE


class GroupListView(ListView):
    def get_object(self):
        group = get_object_or_404(Group, slug=self.kwargs.get('slug'))
        return group

    def get_queryset(self):
        group = self.get_object()
        self.queryset = group.posts
        return self.queryset.all()

    template_name = 'posts/group_list.html'
    paginate_by = POSTS_PER_PAGE

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = context['post']
        symbols_count = 30
        title = f'Пост {post.text[:symbols_count]}'
        author_fullname = f'{post.author.first_name} {post.author.last_name}'
        context['comments'] = post.comments.all()
        context['title'] = title
        context['author_fullname'] = author_fullname
        return context


class PostCreateView(CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'
    extra_context = {'is_edit': False}

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        post = form.save(commit=False)
        post.author = user
        form.save()
        return redirect('posts:profile', user.username)


class PostEditView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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


class AddCommentView(CreateView):
    model = Comment
    form_class = CommentForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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


class FollowIndexView(ListView):
    model = Post
    template_name = 'posts/follow.html'
    paginate_by = POSTS_PER_PAGE

    @method_decorator(login_required())
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        post_list_follow = Post.objects.filter(
            author__following__user=user
        )
        self.queryset = post_list_follow
        return self.queryset


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if author.id is not request.user.id:
        if not request.user.follower.filter(author__username=username):
            Follow.objects.create(
                user=request.user,
                author=author)

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    unfollower = Follow.objects.filter(
        user=request.user,
        author__username=username
    )
    unfollower.delete()
    return redirect('posts:profile', username)
