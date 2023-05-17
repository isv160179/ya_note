import pytest
from django.shortcuts import reverse


@pytest.mark.parametrize(
    'parametrized_client, note_in_list',
    (
            (pytest.lazy_fixture('author_client'), True),
            (pytest.lazy_fixture('admin_client'), False),
    )
)
def test_1_notes_list_for_different_users(
        note, parametrized_client, note_in_list
):
    """
    Тест 1. Отдельная заметка передаётся на страницу со списком заметок
    в списке object_list в словаре context.
    В список заметок одного пользователя не попадают
    заметки другого пользователя.
    """
    url = reverse('notes:list')
    response = parametrized_client.get(url)
    object_list = response.context['object_list']
    assert (note in object_list) is note_in_list


@pytest.mark.parametrize(
    'name, args',
    (
            ('notes:add', None),
            ('notes:edit', pytest.lazy_fixture('slug_for_args'))
    )
)
def test_2_pages_contains_form(author_client, name, args):
    """
    Тест 2. На страницы создания и редактирования заметки передаются формы.
    """
    url = reverse(name, args=args)
    response = author_client.get(url)
    assert 'form' in response.context
