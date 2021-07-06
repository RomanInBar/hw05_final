import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='user')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.author = User.objects.create_user(username='Bob')
        cls.group = Group.objects.create(
            title='текст', slug='slug', description='Это просто очередной тест'
        )
        cls.group_2 = Group.objects.create(
            title='какой-то текст',
            slug='slug_2',
            description='Ёще одна группа',
        )
        for object in range(15):
            cls.post = Post.objects.create(
                text='текст',
                author_id=cls.user.id,
                group_id=cls.group.id,
                image=uploaded,
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.auth_client = Client()
        self.auth_client_2 = Client()
        self.quest_client = Client()
        self.Bob = Client()
        self.auth_client.force_login(ViewsTests.user)
        self.auth_client_2.force_login(ViewsTests.user_2)
        self.Bob.force_login(ViewsTests.author)

    def test_page_use_correct_templates(self):
        """Соответствие шаблонов к url через вызов view."""
        templates_pages = {
            'index.html': reverse('posts:index'),
            'group.html': reverse('group', kwargs={'slug': self.group.slug}),
            'posts/new_edit_post.html': reverse('posts:new_post'),
        }

        for template, page in templates_pages.items():
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertTemplateUsed(
                    response,
                    template,
                    'Ошибка в test_page_use_correct_templates',
                )

    def logic_for_tests(self, value):
        """Логика для тестов главной и страницы профиля."""
        first_object = value.context['page'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_slug = first_object.group.slug
        post_date_0 = first_object.pub_date
        post_image = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_date_0, self.post.pub_date)
        self.assertEqual(post_slug, self.group.slug)
        self.assertEqual(post_image, self.post.image)

    def test_index_page_context(self):
        """Проверка context главной страницы."""
        resp = self.quest_client.get(reverse('posts:index'))
        self.logic_for_tests(resp)

    def test_profile_page_context(self):
        """Проверка context страницы профиля."""
        resp = self.auth_client.get(
            reverse('posts:profile', args=[self.user.username])
        )
        self.logic_for_tests(resp)
        self.assertEqual(resp.context['author'], self.post.author)

    def test_post_correct_context(self):
        """Проверка context страницы поста."""
        response = self.auth_client.get(
            reverse('posts:post', args=[self.user.username, self.post.id])
        )
        resp = response.context['post']
        self.assertEqual(resp.text, self.post.text)
        self.assertEqual(resp.author, self.post.author)
        self.assertEqual(resp.group, self.group)
        self.assertEqual(resp.pub_date, self.post.pub_date)
        self.assertEqual(resp.image, self.post.image)

    def test_new_edit_correct_context(self):
        """Проверка context страницы создания и редактирования поста."""
        response_1 = self.auth_client.get(reverse('posts:new_post'))
        response_2 = self.auth_client.get(
            reverse('posts:post_edit', args=[self.user.username, self.post.id])
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_1.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
                form_field = response_2.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_pages_context(self):
        """Проверка context страницы группы."""
        response = self.auth_client.get(f'/group/{self.group.slug}/')
        post_group = response.context['group']
        post_author = response.context['page'][0]
        self.assertEqual(post_group.title, self.post.text),
        self.assertEqual(post_group.slug, self.group.slug)
        self.assertEqual(post_group.description, self.group.description)
        self.assertEqual(post_author.author, self.post.author)
        self.assertEqual(post_author.image, self.post.image)

    def test_paginator(self):
        """Проверка корректной работы пажинатора."""
        posts_on_page = {
            reverse('posts:index'): (10, 5),
            reverse('group', args=[self.group.slug]): (10, 5),
            reverse('posts:profile', args=[self.user.username]): (10, 5),
        }

        for url, posts in posts_on_page.items():
            first_page, second_page = posts
            with self.subTest(url=url):
                first = self.auth_client.get(url)
                second = self.auth_client.get((url) + '?page=2')
                self.assertEqual(
                    len(first.context.get('page').object_list),
                    first_page,
                    'Ошибка в тесте test_paginator, первая страница',
                )
                self.assertEqual(
                    len(second.context.get('page').object_list),
                    second_page,
                    'Ошибка в тесте test_paginator, вторая страница',
                )

    def test_post_with_group(self):
        """Проверка на запись нового поста с указанием группы."""
        for i in range(2):
            Post.objects.create(
                text='New post',
                group_id=self.group_2.id,
                author_id=self.user.id,
            )

        posts_on_page = {
            reverse('group', args=[self.group.slug]): 10,
            reverse('group', args=[self.group_2.slug]): 2,
        }

        for url, posts in posts_on_page.items():
            with self.subTest(url=url):
                resp = self.auth_client.get(url)
                posts_count = len(resp.context.get('page').object_list)
                self.assertEqual(
                    posts_count, posts, 'Ошибка в тесте test_post_with_group'
                )
        resp = self.auth_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(resp.context.get('page').object_list), 7)

    def test_cache(self):
        """Проверка кэша."""
        resp = self.quest_client.get(reverse('posts:index'))
        content = resp.content
        Post.objects.all().delete()
        resp = self.quest_client.get(reverse('posts:index'))
        self.assertEqual(content, resp.content)
        cache.clear()
        resp = self.quest_client.get(reverse('posts:index'))
        self.assertNotEqual(content, resp.content)

    def test_auth_user_can_follow(self):
        """Возможность подписки авторизованным пользователем."""
        self.auth_client.post(
            reverse("posts:profile_follow", args=[self.author]), follow=True
        )
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.author, self.author)
        self.assertEqual(follow.user, self.user)

    def test_quest_follow(self):
        """
        Неавторизованный пользователь не может подписываться на авторов.
        """
        resp = self.quest_client.post(
            reverse("posts:profile_follow", args=[self.author]), follow=True
        )
        self.assertRedirects(resp, f'/auth/login/?next=/{self.author}/follow/')

    def test_new_post_for_followers(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него.
        """
        Follow.objects.create(user=self.user, author=self.author)
        Post.objects.create(
            text='New Post', author_id=self.author.id, group_id=self.group.id
        )
        first_post = Post.objects.first()
        resp = self.auth_client.get(reverse('posts:follow_index'))
        resp_2 = self.auth_client_2.get(reverse('posts:follow_index'))
        post = resp.context['page'].object_list[0]
        post_2 = resp_2.context['page'].object_list
        self.assertEqual(post, first_post)
        self.assertEqual(len(post_2), 0)

    def test_auth_client_can_comment(self):
        resp = self.auth_client_2.post(
            reverse(
                'posts:add_comment', args=[self.user.username, self.post.id]
            ),
            data={'text': 'New comment'},
            follow=True,
        )
        comment = resp.context['comments'].first()
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(comment.text, 'New comment')
        self.assertEqual(comment.author.id, self.user_2.id)
        self.assertEqual(comment.post.id, self.post.id)
        self.assertEqual(comment.created, Comment.objects.first().created)

    def test_quest_comment(self):
        resp = self.quest_client.post(
            reverse(
                'posts:add_comment', args=[self.user.username, self.post.id]
            )
        )
        self.assertRedirects(
            resp,
            f'/auth/login/?next=/{self.user.username}/{self.post.id}/comment',
        )
