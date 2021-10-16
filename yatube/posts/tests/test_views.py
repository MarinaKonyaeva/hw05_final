from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
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

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.post.author.username
                }): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_pub_date_0 = first_object.pub_date
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_pub_date_0, self.post.pub_date)

    def test_posts_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_pub_date_0 = first_object.pub_date
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_pub_date_0, self.post.pub_date)

    def test_posts_profile_show_correct_content(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}))
        test_author = response.context['author']
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        count_posts_test = response.context['count_posts']
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(test_author, self.authorized_user)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(count_posts_test,
                         self.authorized_user.posts_by_user.all().count())

    def test_posts_post_detail_show_correct_content(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        test_post = response.context['post']
        post_text = test_post.text
        post_author = test_post.author
        post_group = test_post.group
        post_pub_date = test_post.pub_date
        count_posts_test = response.context['count_posts']
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_group, self.post.group)
        self.assertEqual(post_pub_date, self.post.pub_date)
        self.assertEqual(count_posts_test,
                         self.post.author.posts_by_user.all().count())

    def test_posts_create_post_show_correct_content(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_posts_post_with_group_on_index_page(self):
        """Если при созданиии поста указать группу,
        то пост появляется на главной.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        posts_list = response.context['page_obj']
        if self.post.group is not None:
            self.assertIn(self.post, posts_list)

    def test_posts_post_with_group_on_group_list_page(self):
        """Если при созданиии поста указать группу,
        то пост появляется на странице группы.
        """
        if self.post.group is not None:
            response = self.authorized_client.get(
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}))
            posts_list = response.context['page_obj']
            self.assertIn(self.post, posts_list)

    def test_posts_post_with_group_on_profile_page(self):
        """Если при созданиии поста указать группу,
        то пост появляется в профайле пользователя.
        """
        if self.post.group is not None:
            response = self.authorized_client.get(
                reverse('posts:profile',
                        kwargs={'username': self.post.author.username}))
            posts_list = response.context['page_obj']
            self.assertIn(self.post, posts_list)

    def test_posts_post_with_group_not_on_another_group_list_page(self):
        """Если при созданиии поста указать группу,
        то пост не появляется на странице неправильной группы.
        """
        if self.post.group is not None:
            another_group = Group.objects.create(
                title='Еще какая-то группа',
                slug='another-slug',
                description='Описание еще какой-то группы')
            response = self.authorized_client.get(
                reverse('posts:group_list',
                        kwargs={'slug': another_group.slug}))
            posts_list = response.context['page_obj']
            self.assertNotIn(self.post, posts_list)


class PaginatorViewsTest(TestCase):
    # паджинатор нужно тестировать для index, group_list, profile
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.posts_list = []
        for cls.post in range(13):
            test_create_post = Post.objects.create(
                text='Тестовый текст поста',
                author=cls.user,
                group=cls.group,
            )
            cls.posts_list.append(test_create_post)

        cls.reverses_urls = [reverse('posts:index'),
                             reverse('posts:group_list',
                                     kwargs={'slug': cls.group.slug}),
                             reverse('posts:profile',
                                     kwargs={'username': cls.user.username})]

    def test_first_page_contains_ten_records(self):
        for reverse_url in self.reverses_urls:
            response = self.client.get(reverse_url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста.
        for reverse_url in self.reverses_urls:
            response = self.client.get(reverse_url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)


class CacheTests(TestCase):

    def setUp(self):
        self.authorized_user = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        self.post = Post.objects.create(
            text='Тестовый пост для проверки кеширования',
            author=self.authorized_user,
            group=self.group,
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_posts_index_page_cache(self):
        """Cписок записей главной страницы хранится в кеше
        и обновляется раз в 20 секунд.
        """
        # обращаемся к странице первый раз, ожидаем кеширование результата
        first_response = self.authorized_client.get(reverse('posts:index'))
        #  удаляем пост
        Post.objects.get(id=self.post.id).delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        # проверяем, что пост все еще на странице, т.к. закеширован
        self.assertEqual(second_response.content, first_response.content)
        # очищаем кеш и пост исчезает
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(third_response, first_response.content)


class FollowersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='test_1')
        cls.user_2 = User.objects.create_user(username='test_2')
        cls.user_3 = User.objects.create_user(username='test_3')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост для проверки подписок',
            author=cls.user_1,
            group=cls.group,
        )

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_1.username})
        )

    def test_authorized_user_can_follow_authors(self):
        """Авторизованный пользователь может
        подписываться на других пользователей.
        """
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_2, author=self.user_1).exists()
        )

    def test_unauthorized_user_can_not_follow_authors(self):
        """Неавторизованный пользователь не может
        подписываться на других пользователей.
        """
        followers_count = Follow.objects.all().count()
        self.unauthorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_1.username})
        )
        followers_count_check = Follow.objects.all().count()
        self.assertEqual(followers_count, followers_count_check)

    def test_post_on_follow_page_of_follower(self):
        """Новая запись пользователя появляется
        в ленте тех, кто на него подписан.
        """
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        posts_list = response.context['page_obj']
        self.assertIn(self.post, posts_list)

    def test_no_post_on_follow_page_of_non_follower(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто на него не подписан.
        """
        self.authorized_client.force_login(self.user_3)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        posts_list = response.context['page_obj']
        self.assertNotIn(self.post, posts_list)
