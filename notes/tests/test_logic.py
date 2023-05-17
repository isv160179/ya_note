from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    """
    Тестирование логики создания заметок.
    """
    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'note-slug'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.user = User.objects.create(username='Залогиненый пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_1_user_can_create_note(self):
        """
        Тест 1. Залогиненный пользователь может создать заметку.
        """
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с заметками.
        self.assertRedirects(response, self.url_success)
        # Убеждаемся, что есть одна заметка.
        self.assertEqual(Note.objects.count(), 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_2_anonymous_user_cant_create_note(self):
        """
        Тест 2. Анонимный пользователь не может создать заметку.
        """
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        response = self.client.post(self.url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url}'
        # Проверяем, что произошла переадресация на страницу логина:
        self.assertRedirects(response, expected_url)
        # Ожидаем, что записей в базе нет - сравниваем с нулём.
        self.assertEqual(Note.objects.count(), 0)

    def test_2_not_unique_slug(self):
        """
        Тест 3. Невозможно создать две заметки с одинаковым slug.
        """
        for _ in range(2):
            response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_4_empty_slug(self):
        """
        Тест 4. Если при создании заметки не заполнен slug,
        то он формируется автоматически,
        с помощью функции pytils.translit.slugify.
        """
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """
    Тестирование логики редактирования и удаления заметок.
    """
    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'note-slug'
    NEW_NOTE_TITLE = 'Новый заголовок'
    NEW_NOTE_TEXT = 'Новый текст'
    NEW_NOTE_SLUG = 'new-slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.NOTE_SLUG,))
        cls.delete_url = reverse('notes:delete', args=(cls.NOTE_SLUG,))
        cls.success_url = reverse('notes:success')
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.data_form = {
            'text': cls.NEW_NOTE_TEXT,
            'title': cls.NEW_NOTE_TITLE,
            'slug': cls.NEW_NOTE_SLUG,
        }

    def test_5_author_can_edit_note(self):
        """
        Тест 5. Пользователь может редактировать свои заметки.
        """
        # Выполняем запрос на редактирование от имени автора.
        response = self.author_client.post(self.edit_url, data=self.data_form)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.success_url)
        # Обновляем объект.
        self.note.refresh_from_db()
        # Проверяем, что текст измененного поля соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_6_other_user_cant_edit_note(self):
        """
        Тест 6. Пользователь не может редактировать чужие заметки.
        """
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.data_form)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)

    def test_7_author_can_delete_note(self):
        """
        Тест 7. Пользователь может удалить свои заметки.
        """
        # От имени автора отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с комментариями.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.success_url)
        # Ожидаем ноль заметок в системе.
        self.assertEqual(Note.objects.count(), 0)

    def test_8_other_user_cant_delete_note(self):
        """
        Тест 8. Пользователь не может удалить чужие заметки.
        """
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
