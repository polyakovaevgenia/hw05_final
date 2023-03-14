from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


POST_SYMBOLS_NUMBER = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост тестовый пост тестовый пост',
        )

    def test_post_have_correct_object_name(self):
        """Проверяем, что у модели пост корректно работает __str__."""
        post = str(self.post)
        expected_post = self.post.text[:POST_SYMBOLS_NUMBER]
        self.assertEqual(post, expected_post)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_have_correct_object_name(self):
        """Проверяем, что у модели группа корректно работает __str__."""
        group = str(self.group)
        expected_group_name = self.group.title
        self.assertEqual(group, expected_group_name)
