from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Можно начать так: Дорогой, Иван Иванович...',
            'group': 'Выбор подходяще группы - залог количества лайков ❤️',
            'image': 'Загрузите изображение'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
