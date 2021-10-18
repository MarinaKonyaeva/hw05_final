from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def paginator_method(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_BY_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = paginator_method(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    group_post_list = group.posts_by_group.all()
    page_obj = paginator_method(request, group_post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    author_post_list = author.posts_by_user.all()
    count_posts = author_post_list.count()
    page_obj = paginator_method(request, author_post_list)
    user = request.user
    following = user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    context = {
        'author': author,
        'count_posts': count_posts,
        'page_obj': page_obj,
        'following': following or None,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    count_posts = author.posts_by_user.all().count()
    form = CommentForm(request.POST or None)
    comments = post.comments_by_post.all()
    context = {
        'count_posts': count_posts,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save()
        post.save()
        return redirect('posts:post_detail', post_id)
    else:
        form = PostForm(instance=post)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    page_obj = paginator_method(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
