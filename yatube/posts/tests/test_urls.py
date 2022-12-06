from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from ..models import Post, Group


User = get_user_model()


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='test_user_author')
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Группа для теста',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author,
            group=cls.group,
        )


class PostsURLTests(Base):
    """Тестируем доступность страниц приложения Post"""
    def setUp(self):
        self.urls_for_all = [
            '',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        ]
        self.post_edit_url = f'/posts/{self.post.id}/edit/'
        self.post_create_url = '/create/'
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client.force_login(self.user_author)
        cache.clear()

    def test_homepage(self):
        """Smoke Test - домашняя страница доступна"""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_page_without_auth_availability(self):
        urls = self.urls_for_all
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница по адрессу {url} работает неправильно')

    def test_post_edit_author_authorized(self):
        """Страница '/posts/<post_id>/edit' доступна автору поста"""
        self.client = self.authorized_author_client
        response = self.client.get(self.post_edit_url)
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'URL "/create/" работает неприавильно')

    def test_post_edit_authorized(self):
        """Страница '/posts/<post_id>/edit' не доступна не автору поста"""
        self.client = self.authorized_client
        response = self.client.get(self.post_edit_url)
        post_detail = f'/posts/{self.post.id}/'
        self.assertRedirects(
            response, post_detail,
            msg_prefix=(
                'Доступ к редактированию поста '
                'должен иметь только его автор.')
        )

    def test_post_edit_unauthorized(self):
        """Страница '/posts/<post_id>/edit'
        недоступна не авторизованному пользователю"""
        self.client = self.guest_client
        response = self.client.get(self.post_edit_url)
        self.assertRedirects(
            response, ('/auth/login/?next=' + self.post_edit_url),
            msg_prefix=(
                'Доступ к редактированию поста '
                'должен иметь только его автор.')
        )

    def test_create_post_authorized(self):
        self.client = self.authorized_client
        response = self.client.get(self.post_create_url)
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Страница создания поста работает неправильно'
        )

    def test_create_post_unauthorized(self):
        """Неавторизованный пользватель должен перенаправляться
        на страницу авторизации"""
        response = self.guest_client.get(self.post_create_url, follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/',
            msg_prefix=(
                'Неавторизованный пользватель должен перенаправляться '
                'на страницу авторизации')
        )

    def test_unexisting_page(self):
        """Несуществующая страница возвращает статус код 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND,
            'Несуществуюящая страница должна возвращать ошибку 404'
        )


class PostsTemplatesTests(Base):

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client.force_login(self.user_author)
        self.template_pages = {
            'posts/index.html': ['', ],
            'posts/group_list.html': [
                f'/group/{self.group.slug}/',
            ],
            'posts/post_detail.html': [
                f'/posts/{self.post.id}/',
            ],
            'posts/profile.html': [
                f'/profile/{PostsTemplatesTests.user.username}/',
            ],
            'posts/create_post.html': [
                '/create/',
                f'/posts/{self.post.id}/edit/',
            ]
        }
        cache.clear()

    def test_post_template_pages(self):
        self.client = self.authorized_author_client
        for template, urls in self.template_pages.items():
            for url in urls:
                with self.subTest(url=url):
                    response = self.client.get(url)
                    self.assertTemplateUsed(
                        response, template,
                        f'Cтраница {url} использует не корректный шаблон.'
                    )


class CustomErrorPageTemplatesTests(Base):
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.custom_templates = {
            'unexisting_page': 'core/404.html',
            reverse('posts:post_create'): 'core/403csrf.html'
        }

    def test_custom_404error_template(self):
        response = self.authorized_client.get('unexisting_page')
        self.assertTemplateUsed(
            response, 'core/404.html'
        )
