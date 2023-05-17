# test_routes.py
from http import HTTPStatus

import pytest
from django.shortcuts import reverse
from pytest_django.asserts import assertRedirects


# Тест 1. Главная страница доступна анонимному пользователю.
# Страницы регистрации пользователей, входа в учётную запись и
# выхода из неё доступны всем пользователям.
@pytest.mark.parametrize(
    'name',  # Имя параметра функции.
    # Значения, которые будут передаваться в name.
    ('notes:home', 'users:login', 'users:logout', 'users:signup')
)
# Указываем имя изменяемого параметра в сигнатуре теста.
def test_pages_availability_for_anonymous_user(client, name):
    url = reverse(name)  # Получаем ссылку на нужный адрес.
    response = client.get(url)  # Выполняем запрос.
    assert response.status_code == HTTPStatus.OK


# Тест 2. Аутентифицированному пользователю доступна страница
# со списком заметок notes/,
# страница успешного добавления заметки done/,
# страница добавления новой заметки add/.
@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(admin_client, name):
    url = reverse(name)
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


# Тест 3. Страницы отдельной заметки, удаления и редактирования заметки
# доступны только автору заметки. Если на эти страницы попытается
# зайти другой пользователь — вернётся ошибка 404.
@pytest.mark.parametrize(
    # parametrized_client - название параметра,
    # в который будут передаваться фикстуры;
    # Параметр expected_status - ожидаемый статус ответа.
    'parametrized_client, expected_status',
    # В кортеже с кортежами передаём значения для параметров:
    (
            (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
            (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
def test_pages_availability_for_different_users(
        parametrized_client, name, slug_for_args, expected_status
):
    url = reverse(name, args=slug_for_args)
    # Делаем запрос от имени клиента parametrized_client:
    response = parametrized_client.get(url)
    # Ожидаем ответ страницы, указанный в expected_status:
    assert response.status_code == expected_status


# Тест 4. При попытке перейти на страницу списка заметок,
# страницу успешного добавления записи, страницу добавления заметки,
# отдельной заметки, редактирования или удаления заметки
# анонимный пользователь перенаправляется на страницу логина.
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
# Передаём в тест анонимный клиент, name проверяемых страниц и note_object:
def test_redirects(client, name, args):
    login_url = reverse('users:login')
    # Формируем URL в зависимости от того, передан ли объект заметки:
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    # Ожидаем, что со всех проверяемых страниц анонимный клиент
    # будет перенаправлен на страницу логина:
    assertRedirects(response, expected_url)
