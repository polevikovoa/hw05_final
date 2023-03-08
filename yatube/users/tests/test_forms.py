from django.test import Client, TestCase

from posts.forms import PostForm
from posts.models import Post, Group

from django.urls import reverse
from django.contrib.auth.models import User

from users.forms import CreationForm


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Test-User')
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=TaskCreateFormTests.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_user_creation(self):
        """Валидная форма создает запись в Users."""

        user_count = User.objects.count()
        form_data = {
            'username': 'NEO',
            'email': 'neo@matrix.loc',
            'password1': 'Qwerty!@#',
            'password2': 'Qwerty!@#',
        }
        form = CreationForm(form_data)
        self.assertTrue(form.is_valid())
        response = self.authorized_author.post(
            reverse('users:signup'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:index'), status_code=302)
        self.assertEqual(User.objects.count(), user_count + 1)
