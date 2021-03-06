# Generated by Django 2.2.24 on 2021-06-19 01:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0123_contest_rating_elo_mmr'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='show_short_display',
            field=models.BooleanField(default=False, help_text='Whether to show a section containing contest settings on the contest page or not.', verbose_name='show short form settings display'),
        ),
    ]
