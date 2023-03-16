import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow, Comment


User = get_user_model()

FIRST_PAGE_POSTS_COUNT = 10
SECOND_PAGE_POSTS_COUNT = 3
ALL_POSTS_COUNT = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user2 = User.objects.create_user(username='author2')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user2)
        cls.user_follower = User.objects.create_user(username='follower')
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.user_follower)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.group2 = Group.objects.create(
            title='test-group2',
            slug='test-slug2',
            description='test-description2',
        )
        cls.post = Post.objects.create(
            author=cls.user2,
            text='test-post',
            group=cls.group,
        )
        cls.following = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user2,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_follower,
            text='My-comment',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        # cache.clear()

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'author2'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                                                 f'{self.post.pk}'}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.pk}'}):
            'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(response.context['group'], self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'author2'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(response.context['author'], self.user2)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id':
                                                 f'{self.post.pk}'}))
        form_fields = {
            'text': forms.fields.CharField,
        }
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        comments_count = Comment.objects.count()
        self.assertEqual(first_object.comments.count(), comments_count)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.pk}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])

    def test_new_post_create(self):
        """Проверяем новый созданный пост."""
        # тест на отображение на главной странице, в профиле и в группе
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})[0])
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

        response = self.author_client.get(
            reverse('posts:profile', kwargs={'username': 'author2'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_post_with_image(self):
        """Проверяем отображение картинки на страницах."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user2,
            text='test-post',
            group=self.group,
            image=uploaded,
        )
        response = self.author_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})[0])
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, post.image)

        response = self.author_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, post.image)

        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id':
                                                 f'{post.pk}'}))
        first_object = response.context['post']
        self.assertEqual(first_object.image, post.image)

        response = self.author_client.get(reverse('posts:profile',
                                                  kwargs={'username':
                                                          'author2'}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.image, post.image)

    def test_index_cache_page(self):
        """Кеширование в postindex работает."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_content = response.content
        Post.objects.first().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        cached_page_content = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cleared_page_content = response.content
        self.assertEqual(page_content, cached_page_content)
        self.assertNotEqual(cached_page_content, cleared_page_content)

    def test_authorized_client_follower_can_subscribe(self):
        """Авторизованный пользователь может подписываться."""
        self.authorized_client_follower.post(reverse(
            'posts:profile_follow', kwargs={'username': self.user2}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.following.user,
                author=self.following.author
            ).exists()
        )

    def test_authorized_client_follower_can_unsubscribe(self):
        """Авторизованный пользователь может отписываться."""
        self.authorized_client_follower.post(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user2}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.following.user,
                author=self.following.author
            ).exists()
        )

    def test_new_post_for_follower_and_unfollower(self):
        """Проверка отображения поста у не-/подписчика."""
        new_post = Post.objects.create(
            author=self.user2,
            text='test-post-new',
            group=self.group,
        )
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index'))
        self.assertContains(response, new_post)

        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response, new_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cls_atomics = cls._enter_atomics()
        cls.user2 = User.objects.create_user(username='author2')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        for i in range(ALL_POSTS_COUNT):
            cls.post = Post.objects.create(
                author=cls.user2,
                text=f'test-post_{i}',
                group=cls.group,
            )

    def setUp(self):
        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        """Паджинатор на первой странице index работет верно."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         FIRST_PAGE_POSTS_COUNT)

    def test_index_second_page_contains_three_records(self):
        """Паджинатор на второй странице index работет верно."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         SECOND_PAGE_POSTS_COUNT)

    def test_group_list_first_page_contains_ten_records(self):
        """Паджинатор на первой странице group_list работет верно."""
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']),
                         FIRST_PAGE_POSTS_COUNT)

    def test_group_list_second_page_contains_three_records(self):
        """Паджинатор на второй странице group_list работет верно."""
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         SECOND_PAGE_POSTS_COUNT)

    def test_profile_first_page_contains_ten_records(self):
        """Паджинатор на первой странице profile работет верно."""
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': self.user2}))
        self.assertEqual(len(response.context['page_obj']),
                         FIRST_PAGE_POSTS_COUNT)

    def test_profile_second_page_contains_three_records(self):
        """Паджинатор на второй странице profile работет верно."""
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user2}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         SECOND_PAGE_POSTS_COUNT)
