from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


class Created(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        abstract = True


class Post(Created):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Введите текст поста')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор')
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Сообщество',
        help_text='Группа, к которой будет относиться пост',)
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Картинка',
        help_text='Добавть картинку к публикации'
    )

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-created']

    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'post_id': self.pk})

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, max_length=25, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группa'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(Created):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Прокомментированный пост')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор комментария')
    text = models.TextField(verbose_name='Текст комментрия')

    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'post_id': self.post})


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Подписываемый')

    def __str__(self):
        return f'{self.user.username} > {self.author.username}'
