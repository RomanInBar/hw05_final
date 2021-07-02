from django.test import TestCase

from posts.models import Group, Post, User


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый тест титла',
            slug='slug',
            description='Это просто очередной тест',
        )

    def test_title(self):
        """Вывод __str__ метода модели Group."""
        group = GroupModelTest.group
        title = group.title
        self.assertEqual(title, str(group), 'Ошибка в test_title')


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(text='Тестовый текст', author_id=1)

    def test_text(self):
        """Вывод __str__ метода модели Post."""
        post = PostModelTest.post
        text = post.text[:15]
        self.assertEqual(text, str(post), 'Ошиибка в test_text')
