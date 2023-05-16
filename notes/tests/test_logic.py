from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreationEditDelete(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Название заметки'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.NOTE_TEXT,
                         'title': cls.NOTE_TITLE,
                         }

    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество записей.
        notes_count = Note.objects.count()
        # Ожидаем, что записей в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с заметками.
        self.assertRedirects(response, self.url_success)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна заметка.
        self.assertEqual(notes_count, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.author, self.user)

    def test_user_cant_use_not_unique_slug(self):
        SLUG = 'unique_slug'
        self.form_data.update(slug=SLUG)
        for index in range(2):
            self.form_data['title'] = f'{self.NOTE_TITLE} {index}'
            self.form_data['text'] = f'{self.NOTE_TEXT} {index}'
            response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=SLUG + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NOTE_TITLE = 'Название'
    NEW_NOTE_TITLE = 'Новое название'
    NOTE_SLUG = 'note_slag'
    NEW_NOTE_SLUG = 'new_note_slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', kwargs={'slug': cls.NOTE_SLUG})  # URL для редактирования.
        cls.delete_url = reverse('notes:delete', kwargs={'slug': cls.NOTE_SLUG})  # URL для удаления.
        cls.success_url = reverse('notes:success')
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.data_form = {
            'text': cls.NEW_NOTE_TEXT,
            'title': cls.NEW_NOTE_TITLE,
            'slug': cls.NEW_NOTE_SLUG,
        }

    def test_author_can_delete_note(self):
        # От имени автора отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу с комментариями.
        # Заодно проверим статус-коды ответов.
        self.assertRedirects(response, self.success_url)
        # Считаем количество заметок в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль заметок в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
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

    def test_user_cant_edit_note_of_another_user(self):
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
