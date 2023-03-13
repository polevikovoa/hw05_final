from django.db import models
from django.contrib.auth import get_user_model

from posts.constants import ADM_TOOL_TEXT_LIM

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        max_length=200,
        verbose_name="Текст поста",
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        blank=True, null=True,
        verbose_name="Дата публикации"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='posts',
        verbose_name="Автор"
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = "Посты"
        verbose_name_plural = "Посты"
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:ADM_TOOL_TEXT_LIM]


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название группы")
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="URL"
    )
    description = models.TextField(blank=True, verbose_name="Описание группы")

    class Meta:
        verbose_name = "Группы"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title[:ADM_TOOL_TEXT_LIM]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Коментарий')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Создан')

    class Meta:
        ordering = ['-created']
        verbose_name_plural = 'Коментарии'
        verbose_name = 'Коментарий'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_user_author')
        ]
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
