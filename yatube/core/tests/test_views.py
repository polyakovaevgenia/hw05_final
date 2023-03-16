from django.test import TestCase, Client
# from http import HTTPStatus


class ViewTestClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    # def test_error_page(self):
    #     """Страница 404 отдаёт кастомный шаблон."""
    #     response = self.guest_client.get('/nonexist-page/')
    #     self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
    #     self.assertTemplateUsed(response, 'core/404.html')
