Будем тестировать:

**В файле test_routes.py:**

Главная страница доступна анонимному пользователю. 
Страница отдельной записи, ее редактирования и удаления доступны только автору заметки. Авторизованный пользователь не может зайти на эти страницы, если он не является автором заметки.
При попытке анонимного пользователя перейти на страницы посмотреть, добавить, редактировать, удалить заметку, на страницу со списком заметок и на страницу об удачной операции, он переправляется  на страницу авторизации
Страницы регистрации пользователей, входа в учётную запись и выхода из неё доступны анонимным пользователям.

**В файле test_content.py:**

 
**В файле test_logic.py:**

1. При создании заметки попробуем использовать неуникальный слаг:
2. Анонимный пользователь не может создать заметку.
3. Авторизованный пользователь может создать заметку.
4. Авторизованный пользователь может редактировать или удалять свои заметки.
5. Авторизованный пользователь не может редактировать или удалять чужие заметки.