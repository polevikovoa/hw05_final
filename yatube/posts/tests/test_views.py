import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from posts.constants import PAG_PAGE_NUM
from posts.models import Post, Group, Comment, Follow

NUM_OF_POST: int = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_follower = User.objects.create_user(username='Follower_User')
        cls.post_author = User.objects.create_user(username='Author_User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
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
        cls.follow = Follow.objects.create(
            user=cls.post_follower,
            author=cls.post_author,
        )
        for i in range(NUM_OF_POST):
            cls.post = Post.objects.create(
                author=cls.post_author,
                text=('Тестовый пост' + str(i)),
                group=cls.group,
                image=cls.uploaded,
            )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            post=cls.post,
            author=cls.post_author
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.post_follower)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post_author)
        cache.clear()

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.image, self.post.image)
            self.assertEqual(post.id, self.post.id)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон для guest/auth users"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',

            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',

            reverse('posts:profile',
                    kwargs={
                        'username': self.post_author}): 'posts/profile.html',

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
                                kwargs={'username': f'{self.post_author}'}),
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
                                kwargs={'username': f'{self.post_author}'}),
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
        response = self.authorized_author.get(reverse('posts:index'))
        self.check_post_info(response.context['page_obj'][0])

    def test_post_profile_show_correct_context(self):
        """Шаблон Profile сформирован с правильным контекстом."""
        response = self.authorized_follower.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post_author}))

        self.assertEqual(response.context['author'], self.post_author)
        self.check_post_info(response.context['page_obj'][0])
        self.assertEqual(response.context['following'], True)

    def test_post_group_show_correct_context(self):
        """Шаблон Group сформирован с правильным контекстом."""
        page = reverse('posts:group_list',
                       kwargs={'slug': f'{self.group.slug}'})
        response = self.authorized_author.get(page)
        group_context = response.context['group']
        group_title = group_context.title
        group_slug = group_context.slug
        group_description = group_context.description
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_slug, self.group.slug)
        self.assertEqual(group_description, self.group.description)
        self.check_post_info(response.context['page_obj'][0])

    def test_forms_show_correct(self):
        """Проверка коректности формы поста."""
        response_edit = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        url_fields = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id, }),
        }
        for reverse_page in url_fields:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_author.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField)
        self.assertEqual(response_edit.context['is_edit'], True)
        self.check_post_info(response_edit.context['post'])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        context = {response.context['comments'][0].text: self.comment.text,
                   response.context['comments'][0].author: self.post_author,
                   response.context['comments'][0].post: self.post}
        for value, expected in context.items():
            self.assertEqual(context[value], expected)
            self.check_post_info(response.context['post'])

        url_fields = {
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        }
        for reverse_page in url_fields:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_author.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)

    def test_post_added_correctly(self):
        """Проверка создания поста с разными условиями."""
        post = Post.objects.create(
            text='Superman круче Batmena',
            author=self.post_author,
            group=self.group)
        response_set = [
            self.authorized_author.get(reverse('posts:index')),
            self.authorized_author.get(reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'})),
            self.authorized_author.get(reverse('posts:profile', kwargs={
                'username': f'{self.post_author.username}'}))
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
                                   author=self.post_author)
        response_group1 = self.authorized_author.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        group1_posts_context = response_group1.context['page_obj']
        self.assertNotIn(post, group1_posts_context,
                         'поста нет в группе другого пользователя')

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_author.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.post_author,
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
        self.author_client.force_login(self.author)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        already_follows = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).exists()
        self.assertEqual(already_follows, False)
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}))
        already_follows_after = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).exists()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(already_follows_after, True)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        count_follow = Follow.objects.count()
        check_unfollow = Follow.objects.filter(user=self.follower,
                                               author=self.author)
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}))
        self.assertFalse(check_unfollow.exists())
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        Follow.objects.create(
            user=self.follower,
            author=self.author)
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'].object_list)
