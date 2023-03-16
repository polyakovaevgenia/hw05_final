from django.shortcuts import render
from http import HTTPStatus


def page_not_found(request, exception):
    return render(request, 'core/404.html',
                  {'path': request.path}, HTTPStatus.NOT_FOUND, status=404)
# Алексей, если я убираю выше из строчки "status=404" и оставляю только
# HTTPStatus,то у меня не проходят тесты. Тест страницы 404 в
# (posts/tests/test_views.py) отдаёт одновременно
# код 200 и HTTPStatus.NOT_FOUND.
# А если оставить только один тест несуществующей страницы в
# core/tests/test_views.py то ругается pytest, что нет проверки 404 страницы.
# Сделала по stack overflow
# https://stackoverflow.com/questions/14085953/django-404-pages-return-200-status-code


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')


def permission_denied(request, exception):
    return render(request, 'core/403.html', HTTPStatus.FORBIDDEN)


def server_error(request):
    return render(request, 'core/500.html', HTTPStatus.INTERNAL_SERVER_ERROR)
