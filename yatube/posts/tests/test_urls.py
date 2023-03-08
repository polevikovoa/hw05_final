from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.http import HttpResponseForbidden

from posts.models import Post, Group


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.non_author = User.objects.create_user(username='Non-Author')
        cls.author = User.objects.create_user(username='Test-User')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.url_name = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.author.username}/',
            f'/post/{cls.post.id}/',
            f'/posts/{cls.post.id}/edit/',
            f'/posts/{cls.post.id}/comment/',
            '/create/',
        ]

    def setUp(self):
        self.non_author_client = Client()
        self.non_author_client.force_login(self.non_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_url_404(self):
        response = self.client.get('/nothingPage')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_guest_client(self):
        """Доступ неавторизованного пользователя"""
        url_set = ['/',
                   f'/group/{self.group.slug}/',
                   f'/profile/{self.author.username}/',
                   f'/posts/{self.post.id}/',
                   ]
        for page in url_set:
            with self.subTest(page=page):
                response = self.client.get(page)
                error_name = f'Ошибка: нет доступа до страницы {page}'
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 error_name)

    def test_urls_authorized_client(self):
        """Доступ авторизованного пользователя"""
        pages: tuple = ('/create/',
                        f'/posts/{self.post.id}/edit/')
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                error_name = f'Ошибка: нет доступа до страницы {page}'
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 error_name)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя"""
        url_set = {
            reverse('posts:post_create'):
            reverse('users:login') + '?next=' + reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}):
            reverse('users:login') + '?next='
            + reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}),
        }
        for url, value in url_set.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, value)

    def test_urls_redirect_non_author(self):
        """Проверка редактирования поста не автором поста"""
        response_non_author = self.non_author_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}))
        redirect_page = reverse('posts:post_detail', kwargs={
                                'post_id': self.post.pk})
        self.assertRedirects(response_non_author, redirect_page)

    def test_url_uses_correct_template_authorized(self):
        """Проверка использования корректных шаблонов"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_add_comment_redirect_guest_client(self):
        """Редирект неавторизованного пользователя
        при попытке добавить коммент"""
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        redir_url = reverse('users:login') + '?next=' + url
        response = self.client.get(url)
        self.assertRedirects(response, redir_url)

    def test_url_404_uses_custom_template(self):
        response = self.client.get('/nothingPage')
        template = 'core/404.html'
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, template)

    def test_url_403_uses_custom_template(self):
        response = HttpResponseForbidden(reverse('posts:index'))
        self.assertEqual(response.status_code, 403)
