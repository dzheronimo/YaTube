from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, FormView, CreateView, DeleteView
from django.views.generic import UpdateView
from django.urls import reverse
from .models import Group, Post, User, Comment, Follow
from .forms import PostForm, CommentForm


class IndexListView(ListView):
    model = Post
    template_name = 'posts/index.html'
    paginate_by = 10

    @method_decorator(cache_page(20, key_prefix='index_page'))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class GroupListView(ListView):
    def get_object(self):
        group = get_object_or_404(Group, slug=self.kwargs.get('slug'))
        return group

    def get_queryset(self):
        group = self.get_object()
        self.queryset = group.posts
        return self.queryset.all()

    template_name = 'posts/group_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.get_object()
        return context


class ProfileListView(ListView):
    template_name = 'posts/profile.html'
    paginate_by = 10

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return user

    def get_queryset(self):
        user = self.get_object()
        self.queryset = user.posts
        return self.queryset.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.get_object()
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
    paginate_by = 10

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

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.queryset:
            context['follow'] = True
        else:
            context['follow'] = False
        return context


@login_required
def profile_follow(request, username):
    Follow.objects.create(
        user=request.user,
        author=User.objects.get(username=username))

    return redirect('posts:profile', username)
# class ProfileFollow(CreateView):
#     model = Follow
#
#     def get_success_url(self):
#         return reverse('posts:profile', kwargs={'username': self.kwargs.get('username')})
#
#     @method_decorator(login_required())
#     def get_object(self, queryset=None):
#         object = Follow.objects.create(
#             user=self.request.user,
#             author=User.objects.get(id=self.kwargs.get('user_id'))
#         )
#         return object


class ProfileUnfollow(DeleteView):
    model = Follow

    def get_object(self, queryset=None):
        self.object = Follow.objects.filter(
            user=self.request.user,
            author=User.objects.get(username=self.kwargs.get('username'))
        )
        return self.object

@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    ...

# class FollowingsView(ListView):
#     model = Follow
#     template_name = 'posts/index.html'
#     paginate_by = 10
#
#
#
#
# class ProfileFollowView(UpdateView):
#     ...
#
#
# class ProfileUnfollowView(UpdateView):
#     ...