import shutil
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, Group, Comment
from posts.tests.test_views import TEMP_MEDIA_ROOT


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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.fixture_image = SimpleUploadedFile(
            name='new_small.gif',
            content=cls.small_gif,
            content_type='image/gif')

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=TaskCreateFormTests.group,
            image=cls.fixture_image
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        form_data = {
            'text': 'Второй тестовый текст',
            'group': self.group.id,
        }
        # Формирую список ID до создания поста
        initial_post_ids = list(
            Post.objects.all().values_list('id', flat=True))
        # Создаю пост
        response = self.authorized_author.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        # Формирую список ID после создания поста
        fin_post_ids = list(
            Post.objects.all().values_list('id', flat=True))
        # Получаю уникальный ID
        diff_id = list(set(fin_post_ids) - set(initial_post_ids))
        expected_post = Post.objects.get(id=int(diff_id[0]))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(diff_id), 1)
        self.assertEqual(expected_post.text, form_data['text'])
        self.assertEqual(expected_post.group.id, form_data['group'])
        self.assertEqual(expected_post.author, self.post.author)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.post.author}))

    def test_post_edit_forms(self):
        """Валидная форма редактирует запись в БД."""

        # Создаю вторую группу
        group2 = Group.objects.create(title='Тестовая группа2',
                                      slug='test-group2',
                                      description='Описание')

        # Формирую словарь для внесения изменений в форму
        form_data = {'text': 'Текст записанный в форму',
                     'group': group2.id}
        # Формирую запрос на редактирования поста
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        error_post = 'Данные поста не совпадают'

        # Проверка наличия поста с измененными данными
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=group2.id,
            author=self.author,
            pub_date=self.post.pub_date
        ).exists(), error_post)

    def test_create_post_with_image(self):
        """Валидная форма создает запись в Post c Image."""

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        local_image = SimpleUploadedFile(
            name='new_small.gif',
            content=small_gif,
            content_type='image/gif')

        # Create form data with the image file
        form_data = {'text': 'Test Image', 'image': local_image}

        form = PostForm(data=form_data, files=form_data)
        self.assertTrue(form.is_valid())
        form.save()

        post_image = Post.objects.get(id=2)
        error_post = 'Проверь изображение'

        self.assertEqual(Post.objects.count(), 2)
        self.assertTrue(post_image.image, error_post)

    def test_authorized_user_create_comment(self):
        """Проверка создания коментария авторизированным клиентом."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.author)
        form_data = {'text': 'Тестовый коментарий'}
        response = self.authorized_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.author)
        self.assertEqual(comment.post_id, post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail', args={post.id}))

    def test_nonauthorized_user_create_comment(self):
        """Проверка создания комментария не авторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.author)
        form_data = {'text': 'Тестовый коментарий'}
        response = self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.id})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, redirect)
