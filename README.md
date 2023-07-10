# Соцсеть Yatube


### Описание проекта:
Социальная сеть блогеров. Повзоляет написание постов и публикации их в отдельных группах, подписки на посты, добавление и удаление записей и их комментирование. Подписки на любимых блогеров.


### Инструкции по установке
- Клонируйте репозиторий:

```bash
git clone git@github.com:dzheronimo/YaTube.git
```

- Установите и активируйте виртуальное окружение:

для MacOS
```bash
python3 -m venv venv
source venv/bin/activate
```
для Windows
```bash
python -m venv venv
source venv/Scripts/activate
```

- Установите зависимости из файла requirements.txt:
```bash
pip install -r requirements.txt
```

- Примените миграции:
```bash
python manage.py migrate
```

- В папке с файлом manage.py выполните команду:
```bash
python manage.py runserver
```
