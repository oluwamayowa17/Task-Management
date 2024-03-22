# Generated by Django 3.2.5 on 2024-03-21 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0003_remove_subtask_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subtask',
            name='assignees',
            field=models.ManyToManyField(blank=True, related_name='subtasks', to='taskapp.Collaborator', verbose_name='Assign To'),
        ),
        migrations.AlterField(
            model_name='subtask',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Task Name'),
        ),
    ]