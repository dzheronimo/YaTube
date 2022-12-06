from django.test import TestCase


from ..models import Group, Post, User, Comment


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
            text='Тестовый пост12124124124124',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def test_post_have_correct_object_name(self):
        """Проверяем, что у модели Post __str__
        отдает первые 15 символов записи"""
        self.assertLessEqual(
            len(PostModelTest.post.__str__()), 15,
            'Имя объекта модели "Post" больше 15 символов')

    def test_group_str_show_title(self):
        """Проверяем, что у модели Group, __str__ это название группы"""
        self.assertEqual(
            PostModelTest.group.title, PostModelTest.group.__str__(),
            '__str__ модели Group должно быть название Группы'
        )

    def test_post_model_have_verbose_names(self):
        post = PostModelTest.post
        verbose_names = {
            'text': 'Текст',
            'created': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество'
        }

        for field, verbose_name in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, verbose_name,
                    'verbose_names поля {field} выводится неправильно'
                )

    def test_post_model_have_help_texts(self):
        post = PostModelTest.post
        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }

        for field, help_text in help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    help_text,
                    'help_text поля {field} выводится неправильно'
                )

    def test_comment_model_have_verbose_names(self):
        comment = PostModelTest.comment
        verbose_names = {
            'text': 'Текст комментрия',
            'created': 'Дата публикации',
            'author': 'Автор комментария',
            'post': 'Прокомментированный пост'
        }

        for field, verbose_name in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, verbose_name,
                    'verbose_names поля {field} выводится неправильно'
                )
