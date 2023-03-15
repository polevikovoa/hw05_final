from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect

from .constants import PAG_PAGE_NUM
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .utils import do_paginate


def index(request):
    post_model_data = Post.objects.all()
    page_obj = do_paginate(request, post_model_data, PAG_PAGE_NUM)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_model_data = group.posts.all()
    page_obj = do_paginate(request, post_model_data, PAG_PAGE_NUM)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def pagenotfound(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена.</h1>')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    all_author_posts = author.posts.all()
    page_obj = do_paginate(request, all_author_posts, PAG_PAGE_NUM)
    following = request.user.is_authenticated
    if following:
        following = author.following.filter(user=request.user).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        create_post = form.save(commit=False)
        create_post.author = request.user
        create_post.save()
        return redirect('posts:profile', create_post.author)
    template = 'posts/create_post.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template_name = 'posts/post_detail.html'
    comment_form = CommentForm(request.POST or None)
    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, template_name, {'post': post,
                                           'comment_form': comment_form})


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = do_paginate(request, posts, PAG_PAGE_NUM)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(author__username=username,
                          user=request.user).delete()
    return redirect('posts:profile', username)
