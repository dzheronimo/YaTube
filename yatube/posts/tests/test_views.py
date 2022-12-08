import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from django import forms


from ..models import Post, Group, Comment, Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BaseTestClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Описание тестовой группы'
        )

        for i in range(13):
            Post.objects.create(
                text=f'Тестовый пост {(i + 1)}',
                author=cls.user,
                group=cls.group
            )
        cls.post = Post.objects.latest('created')
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

        cls.FIRST_PAGE_POSTS_COUNT = 10
        cls.LAST_PAGE_POSTS_COUNT = 3


class PostsViewsTest(BaseTestClass):

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTest.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_views_use_correct_templates_test(self):
        """Проверяем верный ли шаблон отдают view-функции"""
        post = Post.objects.latest('created')
        views_templates = {
            'posts/index.html': [
                reverse('posts:index'),
            ],
            'posts/group_list.html': [
                reverse(
                    'posts:group_posts',
                    kwargs={'slug': PostsViewsTest.group.slug}),
            ],
            'posts/post_detail.html': [
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': post.id}),
            ],
            'posts/profile.html': [
                reverse(
                    'posts:profile',
                    kwargs={'username': PostsViewsTest.user.username}),
            ],
            'posts/create_post.html': [
                reverse('posts:post_create'),
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': post.id}),
            ]
        }

        for template, reverse_names in views_templates.items():
            for reverses in reverse_names:
                with self.subTest(reverse=reverses):
                    response = self.authorized_client.get(reverses)
                    self.assertTemplateUsed(
                        response, template,
                        f'{reverses} передает не корректный шаблон'
                    )

    def test_homepage_show_correct_context_first_page_paginator(self):
        """Шаблон index возращает правильный context на
        первой странице пагинатора"""
        user = PostsViewsTest.user
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = user.posts.all()[:PostsViewsTest.FIRST_PAGE_POSTS_COUNT]
        for i in range(len(response.context['page_obj'])):
            with self.subTest(post=i):
                self.assertEqual(
                    response.context['page_obj'].object_list[i], first_post[i]
                )

    def test_homepage_show_correct_context_second_page_paginator(self):
        """Шаблон index возращает правильный context
        на второй странице пагинатора"""
        user = PostsViewsTest.user
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        first_post = user.posts.all()[PostsViewsTest.FIRST_PAGE_POSTS_COUNT:]
        for i in range(len(response.context['page_obj'])):
            with self.subTest(post=i):
                self.assertEqual(
                    response.context['page_obj'].object_list[i], first_post[i]
                )

    def test_homepage_first_page_posts_count_paginator(self):
        """Паджинатор передает 10 постов
        в контекст первой страницы posts:index"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']),
            PostsViewsTest.FIRST_PAGE_POSTS_COUNT,
            'Paginator выводит не то количество записей на странице 1'
        )

    def test_homepage_second_page_posts_count_paginator(self):
        """Паджинатор передает 3 постов
        в контекст второй страницы posts:index"""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            PostsViewsTest.LAST_PAGE_POSTS_COUNT,
            'Paginator выводит не то количество записей на последней странице'
        )

    def test_group_posts_show_correct_context(self):
        """Проверка контекста переданного в функцию posts:group_posts"""
        group = PostsViewsTest.group
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': group.slug}))
        posts = PostsViewsTest.group.posts.all()
        self.assertEqual(
            response.context['group'], PostsViewsTest.group,
            ('В контекст страницы /group_posts/ '
             'должен передаваться объект модели Group')
        )
        self.assertEqual(
            response.context['page_obj'].object_list[0], posts[0],
            ('В контекст страницы /group_posts/ '
             'должен передаваться объект модели Post')
        )

    def test_group_post_first_page_posts_count_paginator(self):
        """Проверка работы паджинатора переданного в posts:group_posts"""
        group = PostsViewsTest.group
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': group.slug}))
        self.assertEqual(
            len(response.context['page_obj']),
            PostsViewsTest.FIRST_PAGE_POSTS_COUNT,
            ('Paginator выводит не то количество '
             'записей на странице /group_posts/')
        )

    def test_group_post_second_page_posts_count_paginator(self):
        """Проверка работы паджинатора переданного в posts:group_posts"""
        group = PostsViewsTest.group
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': group.slug}) + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            PostsViewsTest.LAST_PAGE_POSTS_COUNT,
            ('Paginator выводит не то количество '
             'записей на странице /group_posts/?page=2')
        )

    def test_profile_page_show_correct_context(self):
        """Проверяем контекст передаваемый view-функцией posts:profile"""
        user = PostsViewsTest.user
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': user.username}))
        posts = user.posts.all()
        self.assertEqual(
            response.context['author'], user,
            ('В контекст страницы /profile/ '
             'должен передаваться объект модели User')
        )
        self.assertEqual(
            response.context['page_obj'].object_list[0], posts[0],
            ('В контекст страницы /profile/ '
             'должен передаваться объект модели Post')
        )

    def test_profile_first_page_posts_count_paginator(self):
        """Проверяем работу паджинатора на первой странице"""
        user = PostsViewsTest.user
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': user.username}))
        self.assertEqual(
            len(response.context['page_obj']),
            PostsViewsTest.FIRST_PAGE_POSTS_COUNT,
            ('Paginator выводит не то количество '
             'записей на странице /profile/')
        )

    def test_profile_second_page_posts_count_paginator(self):
        """Проверяем работу паджинатора на второй странице"""
        user = PostsViewsTest.user
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': user.username}) + '?page=2')

        self.assertEqual(
            len(response.context['page_obj']),
            PostsViewsTest.LAST_PAGE_POSTS_COUNT,
            ('Paginator выводит не то количество записей '
             'на странице /profile/?page=2')
        )

    def test_post_detail_page_show_correct_context(self):
        """Проверяем контекст передаваемый view-функцией posts:post_detail"""
        post = Post.objects.latest('created')
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id}))
        author_fullname = f'{post.author.first_name} {post.author.last_name}'
        symbols_count = 30
        title = f'Пост {post.text[:symbols_count]}'
        expected_context = {
            'post': post,
            'author_fullname': author_fullname,
            'title': title,
        }

        for value, expected in expected_context.items():
            with self.subTest(value=value):
                self.assertEqual(
                    response.context[value], expected,
                    'Функция posts:post_detail отдает не верный контекст'
                )

    def test_post_edit_show_correct_context(self):
        """Проверяем контекст передаваемый view-функцией posts:edit_post"""
        post = Post.objects.latest('created')
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field, expected,
                    'Функция posts:edit_post отдает не верный контекст'
                )

    def test_create_post_show_correct_context(self):
        """Проверяем контекст передаваемый view-функцией posts:create_post"""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(
                    form_field, expected,
                    'Функция posts:create_post отдает не верный контекст'
                )

    def test_post_with_group_shows_on_homepage(self):
        """Пост с объявленной группой показывается на главной странице"""
        post = Post.objects.latest('created')
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertIn(
            post, response.context.get('page_obj').object_list,
            ('Пост с объявленной группой, '
             'должен отображаться на главной странице')
        )

    def test_post_shows_on_own_groups_page(self):
        """Пост с объявленной группой показывается на странице группы"""
        post = Post.objects.latest('created')
        group = PostsViewsTest.group
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': group.slug})
        )
        self.assertIn(
            post, response.context.get('page_obj').object_list,
            ('Пост с объявленной группой, '
             'должен отображаться на странице группы')
        )

    def test_post_with_group_shows_on_author_profile(self):
        """Пост с объявленной группой показывается в профиле автора"""
        post = Post.objects.latest('created')
        author = PostsViewsTest.user
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': author.username})
        )
        self.assertIn(
            post, response.context.get('page_obj').object_list,
            ('Пост с объявленной группой, '
             'должен отображаться в профиле автора')
        )

    def test_post_with_group_dont_shows_on_another_group_page(self):
        """Пост с объявленной группой показывается на странице группы"""
        post = Post.objects.latest('created')
        another_group = Group.objects.create(
            title='Тестовая другая группа',
            description='Описание другой тестовой группы',
            slug='another_group'
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': another_group.slug})
        )
        self.assertNotIn(
            post, response.context.get('page_obj').object_list,
            ('Пост с объявленной группой, '
             'должен отображаться только на странице своей группы')
        )


class ImageTest(BaseTestClass):
    def setUp(self) -> None:
        self.img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='some.png',
            content=self.img,
            content_type='image/png'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(ImageTest.user)
        cache.clear()

    def test_pages_show_correct_context_with_image(self):
        post_with_img = Post.objects.create(
            author=ImageTest.user,
            text='Тестовый пост',
            group=ImageTest.group,
            image=self.uploaded
        )
        pages_context = [
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': ImageTest.user.username}),
            reverse('posts:group_posts',
                    kwargs={'slug': ImageTest.group.slug}),
        ]

        for reverse_name in pages_context:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                last_post = response.context['page_obj'].object_list[0]
                self.assertEqual(
                    post_with_img.image, last_post.image
                )

    def test_detail_show_correct_context_with_image(self):
        post_with_img = Post.objects.create(
            author=ImageTest.user,
            text='Тестовый пост',
            group=ImageTest.group,
            image=self.uploaded
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': post_with_img.id}))
        self.assertEqual(
            post_with_img.image, response.context['post'].image
        )


class PostCommentTests(BaseTestClass):
    def setUp(self) -> None:
        self.guest_client = Client()
        cache.clear()

    def test_detail_show_correct_context_with_comments(self):
        post = PostCommentTests.post
        comment = PostCommentTests.comment
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id}))
        self.assertIn(
            comment, response.context['comments']
        )


class CacheTests(BaseTestClass):
    def setUp(self) -> None:
        self.guest_client = Client()
        self.post = Post.objects.create(
            author=CacheTests.user,
            text='CacheTesting',
            group=CacheTests.group
        )
        cache.clear()

    def test_index_page_cached_20s(self):
        self.guest_client.get(reverse('posts:index'))
        self.post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(
            self.post.text, response.content.decode('utf8'),
            'Пост должен браться из кеша после удаления'
        )
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotIn(
            self.post.text, response.content.decode('utf8'),
            'После очистки кеша, пост должен удалиться со страницы'
        )


class FollowTests(BaseTestClass):
    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowTests.user)
        self.author = User.objects.create(
            username='test_author'
        )
        self.other_author = User.objects.create(
            username='other_test_author'
        )

    def test_auth_user_can_follow_others_authors(self):
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}))

        self.assertTrue(
            self.user.follower.filter(
                author__username=self.author.username).exists()
        )

    def test_auth_user_can_unfollow_others_authors(self):
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}))

        self.assertFalse(
            self.user.follower.filter(
                author__username=self.author.username).exists()
        )

    def test_new_post_shows_on_follower_feed(self):
        Follow.objects.create(
            user=FollowTests.user,
            author=self.author
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(
            post, response.context['page_obj']
        )

    def test_new_post_dont_shows_on_not_follower_feed(self):
        Follow.objects.create(
            user=FollowTests.user,
            author=self.author
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.author
        )
        self.authorized_client.force_login(self.other_author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(
            post, response.context['page_obj']
        )
