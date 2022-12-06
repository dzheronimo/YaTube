from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


class UsersURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.user = User.objects.create(username='Test_user')
        cls.authorized_client.force_login(cls.user)
        cls.urls = {
            reverse('users:logout'): 'users/logget_out.html',
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'): 'users/password_reset_done.html',
            reverse(
                'users:password_reset_compete'
            ): 'users/password_reset_complete.html',
        }

    def test_urls_httpstatus_ok(self):
        for url in UsersURLTest.urls:
            response = UsersURLTest.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'{url} работает неправильно'
                )

    def test_url_redirect_password_change_unauthorized(self):
        url = reverse('users:password_change')
        response = UsersURLTest.guest_client.get(url, follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/auth/password_change/',
            msg_prefix=('Незарегистрированный пользователь '
                        'Должен перенаправлять на страницу "/login/".')
        )

    def test_url_password_change_authorized_httpstatus_ok(self):
        url = reverse('users:password_change')
        response = UsersURLTest.authorized_client.get(url)
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            f'{url} работает неправильно'
        )

    def test_url_password_change_done_authorized_httpstatus_ok(self):
        url = reverse('users:password_change_done')
        response = UsersURLTest.authorized_client.get(url)
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            f'{url} работает неправильно'
        )

    def test_urls_templates(self):
        for url, template in UsersURLTest.urls.items():
            response = UsersURLTest.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    response, template,
                    f'{url} использует не верный шаблон'
                )

    def test_password_change_tempate(self):
        response = UsersURLTest.authorized_client.get(
            reverse('users:password_change'))
        self.assertTemplateUsed(
            response, 'users/password_change_form.html'
        )

    def test_password_change_done_tempate(self):
        response = UsersURLTest.authorized_client.get(
            reverse('users:password_change_done'))
        self.assertTemplateUsed(
            response, 'users/password_change_done.html'
        )
