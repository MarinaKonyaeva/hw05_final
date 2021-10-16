from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        model = PostModelTest
        str_group = str(model.group)
        str_post = str(model.post)
        models_strs = {
            str_group: model.group.title,
            str_post: model.post.text[:15],
        }
        for model_str, expected_value in models_strs.items():
            with self.subTest(model_str=model_str):
                self.assertEqual(
                    model_str, expected_value)
