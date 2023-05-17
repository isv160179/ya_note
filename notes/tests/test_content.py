from django.contrib.auth import get_user_model
from django.test import TestCase
from django.shortcuts import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    """
    Тестирование контента.
    """

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.slug = (cls.note.slug,)

    def test_1_notes_list_for_different_users(self):
        """
        Тест 1. Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list в словаре context.
        В список заметок одного пользователя не попадают
        заметки другого пользователя.
        """
        users_exams = (
            (self.author, True),
            (self.reader, False),
        )
        url = reverse('notes:list')
        for user, exam in users_exams:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(url)
                object_list = response.context['object_list']
                self.assertIs(self.note in object_list, exam)

    def test_2_pages_contains_form(self):
        """
        Тест 2. На страницы создания и редактирования заметки передаются формы.
        """
        urls = (
            ('notes:add', None),
            ('notes:edit', self.slug)
        )
        self.client.force_login(self.author)
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
