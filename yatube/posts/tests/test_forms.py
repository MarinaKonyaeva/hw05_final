import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.authorized_user,
            group=cls.group,
        )
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'text': 'Тестовый текст - создаем пост через форму',
            'group': cls.group.id,
            'image': cls.uploaded,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        # Отправляем POST-запрос
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        post = Post.objects.get(
            text__exact=self.form_data['text'])
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, self.form_data['text'])
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image.name, f'posts/{self.uploaded.name}')

    def test_edit_post(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста в базе данных."""
        updated_form_data = {
            'text': 'Обновленный текст',
            'group': self.group.id,
        }
        # Отправляем POST-запрос
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=updated_form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.get(id=self.post.id).text,
            updated_form_data['text'])

    def test_unauthorized_user_cannot_create_post(self):
        """Неавторизованный пользователь не может опубликовать пост."""
        posts_count = Post.objects.count()
        response = self.unauthorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={reverse('posts:post_create')}"
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_user = User.objects.create_user(username='auth')
        cls.unauthorized_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.authorized_user)
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.authorized_user,
        )
        cls.form_data = {
            'text': 'Тестовый текст - комментарий к посту',
            'author': cls.authorized_user
        }
        cls.reverse_link = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id})

    def test_authorized_user_can_comment_post(self):
        """Авторизованный пользователь может прокомментировать пост."""
        self.authorized_client.post(
            self.reverse_link,
            data=self.form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.get(text=self.form_data['text']).text,
            self.form_data['text']
        )

    def test_unauthorized_user_cannot_comment_post(self):
        """Неавторизованный пользователь не может прокомментировать пост."""
        comments_count = Comment.objects.count()
        response = self.unauthorized_client.post(
            self.reverse_link,
            data=self.form_data,
            follow=True
        )
        redirect = reverse('users:login')
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response,
            f"{redirect}?next={self.reverse_link}"
        )
