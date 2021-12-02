from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    posts_list = Post.objects.all().select_related('author', 'group')
    paginator = Paginator(posts_list, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    return render(request, 'group.html', {'group': group, 'page': page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    is_following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    context = {'author': author, 'page': page, 'is_following': is_following}
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    form = CommentForm()
    context = {'post': post, 'comments': comments, 'form': form}

    return render(request, 'posts/post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    return render(request, 'posts/new_edit_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect('posts:post', username, post_id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post', username, post_id)
    return render(
        request, 'posts/new_edit_post.html', {'form': form, 'post': post}
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=HTTPStatus.NOT_FOUND,
    )


def server_error(request):
    return render(
        request, 'misc/500.html', status=HTTPStatus.INTERNAL_SERVER_ERROR
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post', username, post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_num = request.GET.get('page')
    page = paginator.get_page(page_num)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.filter(
        user=request.user, author__username=username
    )
    follow.delete()
    return redirect('posts:profile', username)

@login_required
def post_delete(request, username, post_id):
    if username != request.user.username:
        return redirect('/')
    get_object_or_404(Post, id=post_id).delete()
    return redirect('posts:profile', username)
