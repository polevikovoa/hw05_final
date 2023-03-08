from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            '/author/',
            '/tech/',
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_url_404(self):
        """Проверяем несуществующей страницы"""
        response = self.guest_client.get('/nothingPage')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_exists_at_desired_location_authorized(self):
        """Проверяем, что URL валидна по указанному адресу."""

        url_set = ['/about/author/',
                   '/about/tech/',
                   ]
        for url in url_set:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_correct_template_authorized(self):
        """Проверяем шаблоны URL'ов."""

        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',

        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)
