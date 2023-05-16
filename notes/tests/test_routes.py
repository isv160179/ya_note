from http import HTTPStatus
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            text='Текст',
            author=cls.author
        )
        cls.SLUG = {'slug': cls.note.slug}

    def test_pages_availability(self):
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for path_name in urls:
            with self.subTest(path_name=path_name):
                url = reverse(path_name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_pages_for_authorized_users(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            'notes:edit',
            'notes:detail',
            'notes:delete',
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for path_name in urls:
                with self.subTest(user=user, path_name=path_name):
                    url = reverse(path_name, kwargs=self.SLUG)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_user(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:add', None),
            ('notes:edit', self.SLUG),
            ('notes:detail', self.SLUG),
            ('notes:delete', self.SLUG),
            ('notes:list', None),
            ('notes:success', None),
        )
        for path_name, kwargs in urls:
            with self.subTest(path_name=path_name):
                url = reverse(path_name, kwargs=kwargs)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
