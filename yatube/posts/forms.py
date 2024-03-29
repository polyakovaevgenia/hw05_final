from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if 'Инстаграм' in data.lower():
            raise forms.ValidationError('Это слово использовать нельзя!')
        elif 'Отстой' in data.lower():
            raise forms.ValidationError('Это слово использовать нельзя!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
