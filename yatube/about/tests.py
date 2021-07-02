from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Post, User


class AboutTestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Bob")
        cls.post = Post.objects.create(
            text="Какой-то текст", author_id=cls.user.id
        )

    def setUp(self):
        self.quest_client = Client()

    def test_about_app(self):
        """
        Тестирование приложения about,
        проверка доступа неавторизованному пользователю
        и отображения страниц.
        """
        request_urls = {
            "/about/author/": (HTTPStatus.OK, "about/author.html"),
            "/about/tech/": (HTTPStatus.OK, "about/tech.html"),
        }

        for url, value in request_urls.items():
            status, template = value
            with self.subTest(url=url):
                resp = self.quest_client.get(url)
                self.assertEqual(resp.status_code, status)
                self.assertTemplateUsed(resp, template)
