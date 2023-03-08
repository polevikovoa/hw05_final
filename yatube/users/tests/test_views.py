from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from users.forms import CreationForm

from posts.models import Post, Group

User = get_user_model()


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
        for i in range(0, 10):
            cls.post = Post.objects.create(
                author=cls.author,
                text=('Тестовый пост' + str(i)),
                group=TaskPagesTests.group,
            )
        cls.url_name = [
            '/about/author/',
            '/about/tech/',
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_page_uses_correct_template_authorized(self):
        """Проверяем, что во view-функции
        используют правильные html-шаблоны."""

        templates_url_names = {
            'users/signup.html': reverse('users:signup'),
            'users/logged_out.html': reverse('users:logout'),
            'users/login.html': reverse('users:login'),
            'users/password_change_form.html': reverse(
                'users:password_change'),
            'users/password_reset_form.html': reverse('users:password_reset'),
            'users/password_reset_complete.html': reverse(
                'users:password_reset_complete'),
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_form_creation_new_user_authorized(self):
        """Проверяем, что в контексте передаётся
         форма для создания нового пользователя."""

        response = self.guest_client.get(reverse('users:signup'))
        # self.assertContains(response, 'form', count=None, status_code=200,
        #                     msg_prefix='', html=False)
        self.assertIsInstance(response.context['form'], CreationForm)
