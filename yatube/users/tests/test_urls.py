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
        response = self.guest_client.get('/nothingPage')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_exists_at_desired_location_authorized(self):
        url_set = ['/auth/password_change/',
                   '/auth/password_change/done/',
                   '/auth/password_reset/',
                   '/auth/password_reset/done/',
                   '/auth/reset/<uidb64>/<token>/',
                   '/auth/signup/',
                   '/auth/logout/',
                   '/auth/login/',
                   '/auth/reset/done/',
                   ]
        for url in url_set:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_correct_template_authorized(self):
        templates_url_names = {
            'users/signup.html': '/auth/signup/',
            'users/logged_out.html': '/auth/logout/',
            'users/login.html': '/auth/login/',
            'users/password_change_form.html': '/auth/password_change/',
            'users/password_reset_form.html': '/auth/password_reset/',

        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)
