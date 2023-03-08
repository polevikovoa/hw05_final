from http import HTTPStatus

import shutil
import tempfile

from django.conf import settings
from django import forms
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.constants import PAG_PAGE_NUM
from posts.forms import CommentForm
from posts.models import Post, Group, Comment, Follow

NUM_OF_POST: int = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Test-User')
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        for i in range(NUM_OF_POST):
            cls.post = Post.objects.create(
                author=cls.author,
                text=('Тестовый пост' + str(i)),
                group=TaskPagesTests.group,
                image=cls.uploaded,
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон для guest/auth users"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',

            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',

            reverse('posts:profile',
                    kwargs={'username': self.author}): 'posts/profile.html',

            reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk}): 'posts/post_detail.html',

            reverse('posts:post_create'): 'posts/create_post.html',

            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_correct_page1_post_count_guest_client(self):
        """Проверка количества постов на index и profile страницах."""
        pages: tuple = (reverse('posts:index'),
                        reverse('posts:profile',
                                kwargs={'username': f'{self.author}'}),
                        reverse('posts:group_list',
                                kwargs={'slug': f'{self.group.slug}'}))
        for page in pages:
            with self.subTest(page=page):
                response1 = self.authorized_author.get(page)
                count_posts1 = len(response1.context['page_obj'])
                error_page1 = (f'Ошибка: {count_posts1} постов,'
                               f'должно {PAG_PAGE_NUM}')
                self.assertEqual(count_posts1, PAG_PAGE_NUM, error_page1)

    def test_correct_page2_post_count_guest_client(self):
        """Проверка количества постов на index и profile страницах."""
        pages: tuple = (reverse('posts:index'),
                        reverse('posts:profile',
                                kwargs={'username': f'{self.author}'}),
                        reverse('posts:group_list',
                                kwargs={'slug': f'{self.group.slug}'}))
        for page in pages:
            with self.subTest(page=page):
                response2 = self.authorized_author.get(page + '?page=2')
                count_posts2 = len(response2.context['page_obj'])
                error_page2 = (f'Ошибка: {count_posts2} постов,'
                               f'должно {NUM_OF_POST - PAG_PAGE_NUM}')
                self.assertEqual(count_posts2, NUM_OF_POST - PAG_PAGE_NUM,
                                 error_page2)

    def test_post_index_show_correct_context(self):
        """Шаблон Index сформирован с правильным контекстом."""
        page = reverse('posts:index')
        response = self.authorized_author.get(page)
        context_object = response.context['page_obj'][0]
        index_id = context_object.id
        index_author = context_object.author
        index_group = context_object.group
        index_post_text = context_object.text
        self.assertEqual(index_id, self.post.pk)
        self.assertEqual(index_author, self.author)
        self.assertEqual(index_group, self.group)
        self.assertEqual(index_post_text, self.post.text)

    def test_post_group_show_correct_context(self):
        """Шаблон Group сформирован с правильным контекстом."""
        page = reverse('posts:group_list',
                       kwargs={'slug': f'{self.group.slug}'})
        response = self.authorized_author.get(page)
        group_context = response.context['group']
        page_obj_context = response.context['page_obj'][0]
        group_title = group_context.title
        group_slug = group_context.slug
        group_description = group_context.description
        post_text = page_obj_context.text
        post_author = page_obj_context.author
        post_group = page_obj_context.group
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_slug, self.group.slug)
        self.assertEqual(group_description, self.group.description)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.author)
        self.assertEqual(post_group, self.group)

    def test_post_profile_show_correct_context(self):
        """Шаблон Profile сформирован с правильным контекстом."""
        page = reverse('posts:profile', kwargs={'username': f'{self.author}'})
        response = self.authorized_author.get(page)
        author_context = response.context['author']
        page_obj_context = response.context['page_obj'][0]
        profile_username = author_context.username
        post_text = page_obj_context.text
        post_author = page_obj_context.author
        post_group = page_obj_context.group
        self.assertEqual(profile_username, self.author.username)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.author)
        self.assertEqual(post_group, self.group)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = {response.context['post'].text: self.post.text,
                response.context['post'].group: self.group,
                response.context['post'].author: self.author}
        for value, expected in post.items():
            self.assertEqual(post[value], expected)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly(self):
        """Проверка создания поста с разными условиями."""
        post = Post.objects.create(
            text='Superman круче Batmena',
            author=self.author,
            group=self.group)
        response_set = [
            self.authorized_author.get(reverse('posts:index')),
            self.authorized_author.get(reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'})),
            self.authorized_author.get(reverse('posts:profile', kwargs={
                'username': f'{self.author.username}'}))
        ]
        for response in response_set:
            with self.subTest(response=response):
                expect = response.context['page_obj'][0]
                self.assertEqual(expect, post)

    def test_post_not_another_group(self):
        """Проверяем, что пост не попал в группу,
        для которой не был предназначен."""
        group2 = Group.objects.create(title='группа №2',
                                      slug='test_group2')
        post = Post.objects.create(text='Пост в группе 1',
                                   group=group2,
                                   author=self.author)
        response_group1 = self.authorized_author.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        group1_posts_context = response_group1.context['page_obj']
        self.assertNotIn(post, group1_posts_context,
                         'поста нет в группе другого пользователя')

    def test_context_image_create(self):
        """Проверяем, что изображение передается в контексте"""
        pages: tuple = (reverse('posts:index'),
                        reverse('posts:profile',
                                kwargs={'username': f'{self.author}'}),
                        reverse('posts:group_list',
                                kwargs={'slug': f'{self.group.slug}'}))
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_author.get(page)
                context_obj = response.context['page_obj'].object_list[0]
                error_post = 'Пост с картинкой отсутствует'
                self.assertTrue(context_obj.image, error_post)
                self.assertTrue(Post.objects.filter(
                    text=self.post.text,
                    image=self.post.image,
                ).exists(), error_post)

    def test_context_image_post_id(self):
        """Проверяем, что изображение передается в контексте"""
        page = reverse('posts:post_detail',
                       kwargs={'post_id': f'{self.post.id}'})
        response = self.authorized_author.get(page)
        context_obj = response.context['post']
        error_post = 'Пост с картинкой отсутствует'
        self.assertTrue(context_obj.image, error_post)

    def test_context_post_comment(self):
        """Проверяем, что комментарий передается в контексте"""
        form_data = {
            'text': 'Test Comment',
            'author': self.author.id,
            'post': self.post.id
        }
        form = CommentForm(data=form_data)
        new_comment = form.save(commit=False)
        new_comment.author = self.author
        new_comment.post = self.post
        self.assertTrue(form.is_valid())
        new_comment.save()
        page = reverse('posts:post_detail',
                       kwargs={'post_id': f'{self.post.id}'})
        response = self.authorized_author.get(page)
        context_obj = response.context['comments']
        post_comment = Comment.objects.all()
        error_post = 'Комментарий отсутствует'
        self.assertTrue(context_obj, error_post)
        self.assertTrue(post_comment, error_post)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_author.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )
        response_old = self.authorized_author.get(reverse('posts:index'))
        old_posts = response_old.content
        cache.clear()
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_author.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='post_author',
        )
        cls.follower = User.objects.create(
            username='post_follower',
        )
        cls.post = Post.objects.create(
            text='Финальное задание. Спринт 6. Подпишись!',
            author=cls.author,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.author)

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.follower.id)
        self.assertEqual(follow.user_id, self.author.id)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.author,
            author=self.follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(
            author=self.author,
            text="Подпишись на меня")
        Follow.objects.create(
            user=self.follower,
            author=self.author)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            author=self.author,
            text="Подпишись на меня")
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
