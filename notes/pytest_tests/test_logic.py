from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.shortcuts import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


def test_1_user_can_create_note(author_client, author, form_data):
    """
    Тест 1. Залогиненный пользователь может создать заметку.
    """
    url = reverse('notes:add')
    response = author_client.post(url, data=form_data)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    assert new_note.title == form_data['title']
    assert new_note.text == form_data['text']
    assert new_note.slug == form_data['slug']
    assert new_note.author == author


@pytest.mark.django_db
def test_2_anonymous_user_cant_create_note(client, form_data):
    """
    Тест 2. Анонимный пользователь не может создать заметку.
    """
    url = reverse('notes:add')
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Note.objects.count() == 0


def test_3_not_unique_slug(author_client, note, form_data):
    """
    Тест 3. Невозможно создать две заметки с одинаковым slug.
    """
    url = reverse('notes:add')
    form_data['slug'] = note.slug
    response = author_client.post(url, data=form_data)
    assertFormError(response, 'form', 'slug', errors=(note.slug + WARNING))
    assert Note.objects.count() == 1


def test_4_empty_slug(author_client, form_data):
    """
    Тест 4. Если при создании заметки не заполнен slug,
    то он формируется автоматически,
    с помощью функции pytils.translit.slugify.
    """
    url = reverse('notes:add')
    form_data.pop('slug')
    response = author_client.post(url, data=form_data)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    expected_slug = slugify(form_data['title'])
    assert new_note.slug == expected_slug


def test_5_author_can_edit_note(author_client, form_data, note):
    """
    Тест 5. Пользователь может редактировать свои заметки.
    """
    url = reverse('notes:edit', args=(note.slug,))
    response = author_client.post(url, form_data)
    assertRedirects(response, reverse('notes:success'))
    note.refresh_from_db()
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']


def test_6_other_user_cant_edit_note(admin_client, form_data, note):
    """
    Тест 6. Пользователь не может редактировать чужие заметки.
    """
    url = reverse('notes:edit', args=(note.slug,))
    response = admin_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    note_from_db = Note.objects.get(id=note.id)
    assert note.title == note_from_db.title
    assert note.text == note_from_db.text
    assert note.slug == note_from_db.slug


def test_7_author_can_delete_note(author_client, slug_for_args):
    """
    Тест 7. Пользователь может удалить свои заметки.
    """
    url = reverse('notes:delete', args=slug_for_args)
    response = author_client.post(url)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 0


def test_8_other_user_cant_delete_note(admin_client, form_data, slug_for_args):
    """
    Тест 8. Пользователь не может удалить чужие заметки.
    """
    url = reverse('notes:delete', args=slug_for_args)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Note.objects.count() == 1
