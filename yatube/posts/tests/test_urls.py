from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user2 = User.objects.create_user(username='author2')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            author=cls.user2,
            text='test-post',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_home_page_exists(self):
        """Страница homepage доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_page_exists(self):
        """Страница grouppage доступна любому пользователю."""
        response = self.guest_client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_page_exists(self):
        """Страница profilepage доступна любому пользователю."""
        response = self.guest_client.get(
            f'/profile/{self.post.author.username}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_page_exists(self):
        """Страница postpage доступна любому пользователю."""
        response = self.guest_client.get(f'/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_page_exists(self):
        """Страница postcreatepage доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_page_exists(self):
        """Страница posteditpage доступна автору поста."""
        response = self.author_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_page_redirect_anonymous_on_admin_login(self):
        """Страница postcreatepage перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/', Follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_page_redirect_authorized_on_post_detail(self):
        """Страница posteditpage перенаправит авторизованного пользователя."""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/', Follow=True)
        self.assertRedirects(
            response, f'/posts/{self.post.pk}/'
        )

    def test_page_not_exists(self):
        """Страница не доступна."""
        response = self.guest_client.get('/posts/not-exist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_page_not_exists(self):
        """Страница edit не доступна зарегистрированному не автору поста."""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def add_comment_page_not_exists_for_guest(self):
        """Страница addcomment недоступна неавторизованному пользователю."""
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def add_comment_page_for_authorized_client(self):
        """Страница addcomment доступна авторизованному пользователю."""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
