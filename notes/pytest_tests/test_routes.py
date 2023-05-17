# test_routes.py
from http import HTTPStatus

import pytest
from django.shortcuts import reverse
from pytest_django.asserts import assertRedirects


@pytest.mark.parametrize(
    'name',
    ('notes:home', 'users:login', 'users:logout', 'users:signup')
)
def test_1_pages_availability_for_anonymous_user(client, name):
    """
    Тест 1. Главная страница доступна анонимному пользователю.
    Страницы регистрации пользователей, входа в учётную запись и выхода
    из неё доступны всем пользователям.
    """
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_2_pages_availability_for_auth_user(admin_client, name):
    """
    Тест 2. Аутентифицированному пользователю доступна страница
    со списком заметок notes/,
    страница успешного добавления заметки done/,
    страница добавления новой заметки add/.
    """
    url = reverse(name)
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
            (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
            (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
def test_3_pages_availability_for_different_users(
        parametrized_client, name, slug_for_args, expected_status
):
    """
    Тест 3. Страницы отдельной заметки, удаления и редактирования заметки
    доступны только автору заметки. Если на эти страницы попытается
    зайти другой пользователь — вернётся ошибка 404.
    """
    url = reverse(name, args=slug_for_args)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args',
    (
            ('notes:detail', pytest.lazy_fixture('slug_for_args')),
            ('notes:edit', pytest.lazy_fixture('slug_for_args')),
            ('notes:delete', pytest.lazy_fixture('slug_for_args')),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
    ),
)
def test_4_redirects(client, name, args):
    """
    Тест 4. При попытке перейти на страницу списка заметок,
    страницу успешного добавления записи, страницу добавления заметки,
    отдельной заметки, редактирования или удаления заметки
    анонимный пользователь перенаправляется на страницу логина.
    """
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
