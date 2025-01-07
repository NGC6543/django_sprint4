from django.db import models


MAX_LENGTH = 256


class IsPublishedAndCreatedModel(models.Model):
    """Абстрактный класс для наследования
    полей is_published и created_at.
    """

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class TitleModel(models.Model):
    """Абстрактный класс для наследования
    поля title.
    """

    title = models.CharField('Заголовок', max_length=MAX_LENGTH)

    class Meta:
        abstract = True
