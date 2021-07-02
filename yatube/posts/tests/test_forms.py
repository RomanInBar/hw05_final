import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class CreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='user')

        cls.group = Group.objects.create(
            title='группа-1', slug='slug', description='первая группа'
        )
        cls.group_2 = Group.objects.create(
            title='группа-2', slug='slug_2', description='вторая группа'
        )
        cls.post = Post.objects.create(
            text='текст', author_id=cls.user.id, group_id=cls.group.id
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(CreateFormTest.user)

    def test_create_post(self):
        """Запись новых постов в базу данных."""
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )

        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )

        form_data = {
            'text': 'New post',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.auth_client.post(
            reverse('posts:new_post'), data=form_data, follow=True
        )

        post = Post.objects.filter(text=form_data['text']).get()

        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=post.text, group=post.group, image=post.image
            )
        )

    def test_edit_post(self):
        """Редактирование поста."""
        post_count = Post.objects.count()
        form_fields = {'text': 'Редачим пост', 'group': self.group_2.id}
        resp = self.auth_client.post(
            reverse(
                'posts:post_edit', args=[self.user.username, self.post.id]
            ),
            data=form_fields,
            follow=True,
        )
        edit_post = Post.objects.first()

        var_tests = {
            form_fields['text']: edit_post.text,
            form_fields['group']: edit_post.group.id,
            Post.objects.count(): post_count,
            resp.status_code: HTTPStatus.OK,
        }

        for var_one, var_two in var_tests.items():
            with self.subTest(var_one=var_one):
                self.assertEqual(var_one, var_two)
