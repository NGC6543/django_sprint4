# Описание

Блог, в котором пользователи могут создавать публикации по определенным категориям и комментировать другие публикации. Реализована система регистрации.
Категории может создавать только админ.

# Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```bash
https://github.com/NGC6543/django_sprint4.git
```

```bash
cd django_sprint4
```

## Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
```
source env/bin/activate
```

## Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```

## Выполнить миграции:
```
python3 manage.py migrate
```
## Запустить проект:
```
python3 manage.py runserver
```

# Стек технологий:
- Python
- Django
- SQL
- HTML
- CSS
