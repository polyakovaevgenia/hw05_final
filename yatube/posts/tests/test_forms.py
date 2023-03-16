import shutil
import tempfile

from posts.models import Post, Group, Comment

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor5')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.group5 = Group.objects.create(
            title='test-title5',
            slug='test-slug5',
            description='test-description5',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user2 = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test-text5',
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'TestAuthor5'}))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=None
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует пост."""
        post = Post.objects.create(
            author=self.user,
            text='test-text61',
            group=self.group5,
        )
        form_data_new = {
            'text': 'test-text test text',
            'group': 'test-group-test-group',
        }
        self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk, }),
            data=form_data_new,
            follow=True,)

        edited_post = Post.objects.get(id=1)
        self.assertNotEqual(edited_post.text, form_data_new['text'])
        self.assertNotEqual(edited_post.group, form_data_new['group'])
        self.assertEqual(edited_post.author, post.author)
        self.assertEqual(edited_post.pub_date, post.pub_date)

    def test_edit_post_guest_client(self):
        """Неавторизованный клиент не может редактировать пост."""
        post = Post.objects.create(
            author=self.user,
            text='test-text6189',
            group=self.group5,
        )
        form_data_new = {
            'text': 'test-text test text6189',
            'group': 'test-group test-group',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk, }),
            data=form_data_new,
            follow=True,)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )
        self.assertTrue(
            Post.objects.filter(
                text=post.text,
                author=post.author,
                group=post.group,
                pub_date=post.pub_date
            ).exists()
        )

    def test_edit_post_guest_client(self):
        """Не автор поста не может редактировать пост."""
        post = Post.objects.create(
            author=self.user,
            text='test-text6189',
            group=self.group5
        )
        form_data_new = {
            'text': 'test-text test text6189',
            'group': 'test-group test-group',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk, }),
            data=form_data_new,
            follow=True,)
        self.assertRedirects(
            response, f'/posts/{post.pk}/'
        )
        self.assertTrue(
            Post.objects.filter(
                text=post.text,
                author=post.author,
                group=post.group,
                pub_date=post.pub_date
            ).exists()
        )

    def test_create_post_guest_client(self):
        """Неавторизованный пользователь не может создать пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test-text5',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)

        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

        self.assertEqual(Post.objects.count(), posts_count)

    def new_post_create_group(self):
        """У нового поста есть группа."""
        form_fields = {
            'text': 'Hello. It is new post',
            'group': 'Group one',
        }
        response = self.author_client.post(reverse('posts:post_create'),
                                           data=form_fields,
                                           follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'TestAuthor5'}))
        self.assertTrue(
            Post.objects.filter(
                text=form_fields['text'],
                author=self.user,
                group=form_fields['group']
            ).exists()
        )

    def test_new_post_with_img(self):
        """Проверка создания поста с картинкой."""
        posts_count = Post.objects.count()
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
        form_fields = {
            'text': 'Hello. It is new post',
            'image': uploaded,
        }
        response = self.author_client.post(reverse('posts:post_create'),
                                           data=form_fields,
                                           follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'TestAuthor5'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text=form_fields['text'],
                                image='posts/small.gif',
                                author=self.user,
                                group=None).exists()
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.guest_client = Client()

    def test_add_comment(self):
        """Валидная форма создает комментарий."""
        post = Post.objects.create(
            author=self.user,
            text='test-text61'
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'test-text-text',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk, }),
            data=form_data,
            follow=True,)

        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': post.pk, })),
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=form_data['text'],).exists()
        )

    def test_guest_can_not_add_comment(self):
        """Неавторизованный пользователь не может создает комментарий."""
        post = Post.objects.create(
            author=self.user,
            text='test-text61'
        )
        form_data = {
            'text': 'test-text-text-guest',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk, }),
            data=form_data,
            follow=True,)

        self.assertFalse(
            Comment.objects.filter(text=form_data['text'],).exists()
        )
