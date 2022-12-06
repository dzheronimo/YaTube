from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse


class AboutStaticPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.static_pages = {
            'about/author.html': [reverse('about:author'), ],
            'about/tech.html': [reverse('about:tech'), ],
        }

    def test_about_pages_HTTPStatusOK(self):
        static_pages = AboutStaticPagesTest.static_pages
        for urls in static_pages.values():
            for url in urls:
                response = AboutStaticPagesTest.guest_client.get(url)
                with self.subTest(url=url):
                    self.assertEqual(
                        response.status_code, HTTPStatus.OK,
                        f'Страница {url} работатет неправильно'
                    )

    def test_about_pages_templates(self):
        static_pages = AboutStaticPagesTest.static_pages
        for template, urls in static_pages.items():
            for url in urls:
                response = AboutStaticPagesTest.guest_client.get(url)
                with self.subTest(url=url):
                    self.assertTemplateUsed(
                        response, template,
                        f'Страница {url} использует неверный шаблон.'
                    )
