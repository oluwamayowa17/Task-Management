# Generated by Django 3.2.5 on 2024-03-25 11:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0008_project_collaborator'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collaborator', models.EmailField(max_length=254)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='taskapp.project')),
            ],
            options={
                'unique_together': {('collaborator', 'project')},
            },
        ),
        migrations.AddField(
            model_name='subtask',
            name='collaborator',
            field=models.ManyToManyField(blank=True, related_name='subtasks', to='taskapp.Invitation', verbose_name='Assign To'),
        ),
    ]
