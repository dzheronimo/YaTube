from ..forms import PostForm
from ..models import Post, Group

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
            slug='test_group'
        )
        cls.another_group = Group.objects.create(
            title='Другая группа',
            description='Описание другой группы',
            slug='another_group'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)
        self.form = PostForm()

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
            'group': PostFormTests.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={
                    'username': PostFormTests.user.username}),
            msg_prefix=(
                f'{response.context.get("url")}После отправки формы должен '
                f'вызываться редирект на профайл автора')
        )
        self.assertEqual(
            Post.objects.count(), posts_count + 1,
            'При отправке формы должен создаваться объект модели Post')
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTests.user.id,
                text=form_data['text'],
                group=PostFormTests.group
            ).exists(),
            'Форма должна создавать объект модели Post'
        )

    def test_post_not_create_unauthorized_user(self):
        """Неавторизованный пользователь не может создавать посты"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Test',
            'group': PostFormTests.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        self.assertNotEqual(
            Post.objects.count(), (posts_count + 1)
        )

    def test_edit_post(self):
        """Изменения при редактировании поста должны сохраняться в БД"""
        form_data = {
            'text': 'Отредактированный пост',
            'group': PostFormTests.another_group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': PostFormTests.post.id})
        )
        PostFormTests.post.refresh_from_db()
        self.assertEqual(
            PostFormTests.post.text, form_data['text']
        )
        self.assertEqual(
            PostFormTests.post.group.pk, form_data['group']
        )

    def test_post_cannot_edit_unathorized_user(self):
        """Неавторизованный пользователь не может редактировать посты"""
        form_data = {
            'text': 'Отредактированный пост',
            'group': PostFormTests.another_group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, (f'/auth/login/?next='
                       f'/posts/{PostFormTests.post.id}/edit/')
        )
        PostFormTests.post.refresh_from_db()
        self.assertNotEqual(
            PostFormTests.post.text, form_data['text']
        )

    def test_post_cannot_edit_not_author(self):
        """Редактировать пост может только его автор"""
        not_author_user = User.objects.create(
            username='Im_not_author'
        )
        self.authorized_client.force_login(not_author_user)
        form_data = {
            'text': 'Отредактировал пост',
            'group': PostFormTests.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.id})
        )
        PostFormTests.post.refresh_from_db()
        self.assertNotEqual(
            PostFormTests.post.text, form_data['text']
        )

    def test_signup_creates_user_model(self):
        """При авторизации создается модель User()"""
        users_count = User.objects.count()
        form_data = {
            'username': 'TestUser_2',
            'password1': 'testpassword',
            'password2': 'testpassword'
        }
        response = self.authorized_client.post(
            reverse('users:signup'), data=form_data, follow=True)
        self.assertRedirects(
            response, reverse('posts:index'),
        )
        self.assertEqual(
            User.objects.count(), users_count + 1
        )
        self.assertTrue(
            User.objects.filter(username='TestUser_2').exists(),
            'Тестовый пользователь небыл создан'
        )

    def test_post_comment_create_authorized_user(self):
        post = PostFormTests.post
        comments_count = post.comments.count()
        form_data = {
            'text': 'Комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': post.id}),
            data=form_data, follow=True)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': post.id})
        )
        self.assertEqual(
            post.comments.count(), (comments_count + 1)
        )
        self.assertTrue(
            post.comments.filter(
                text=form_data['text']
            ).exists()
        )

    def test_post_comment_cannot_create_not_authorized_user(self):
        post = PostFormTests.post
        comments_count = post.comments.count()
        form_data = {
            'text': 'Комментарий'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': post.id}),
            data=form_data, follow=True)
        self.assertRedirects(
            response,
            (reverse('users:login')
             + '?next=' + reverse('posts:add_comment',
                                  kwargs={'post_id': post.id}))
        )
        self.assertNotEqual(
            post.comments.count(), (comments_count + 1)
        )
        self.assertFalse(
            post.comments.filter(
                text=form_data['text']
            ).exists()
        )
