from django.contrib.auth.models import User
from django.test import TestCase

from ..constants import ADM_TOOL_TEXT_LIM
from ..models import Group, Post, Follow, Comment


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост в котором больше 15 символов.',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        models = [
            (str(post), post.text[:ADM_TOOL_TEXT_LIM]),
            (str(group), group.title[:ADM_TOOL_TEXT_LIM])
        ]
        error_name = f"Вывод не имеет {ADM_TOOL_TEXT_LIM} символов"

        for model, expected_output in models:
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_output, error_name)

    def test_verbose_name(self):
        """verbose_name полей совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'author': 'Автор',
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text полей совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2,
        )

    def test_follow_str(self):
        """Проверка __str__ у follow."""
        self.assertEqual(
            f'{self.follow.user} подписался на {self.follow.author}',
            str(self.follow))

    def test_follow_verbose_name(self):
        """Проверка verbose_name у follow."""
        field_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.follow._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Alisa')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Коммент для поста',
            author=cls.user,
            post=cls.post,
        )

    def test_сomment_str(self):
        """Проверка __str__ у сomment."""
        self.assertEqual(self.comment.text[:15], str(self.comment))

    def test_сomment_verbose_name(self):
        """Проверка verbose_name у сomment."""
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Коментарий',
            'created': 'Создан',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)
