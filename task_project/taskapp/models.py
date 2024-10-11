from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from account.models import User
   

class Collaborator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


class Project(models.Model):
    TO_DO = "PENDING"
    IN_PROGRESS = "IN PROGRESS"
    COMPLETED = "COMPLETED"

    STATUS_CHOICE = [
        (TO_DO, "PENDING"),
        (IN_PROGRESS, "IN PROGRESS"),
        (COMPLETED, "COMPLETED")
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name = "Project Name")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICE, default=TO_DO)
    collaborator = models.ManyToManyField(Collaborator, related_name='projects', verbose_name='Collaborators', blank=True)
    due_date = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.name 
    
    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        return super().save(*args, **kwargs)
    

class Invitation(models.Model):
    collaborator = models.EmailField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    accepted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True) 

    class Meta:
        unique_together = ('collaborator', 'project')

    def __str__(self):
        return self.collaborator

class SubTask(models.Model):
    TO_DO = "PENDING"
    ON_IT = "ON IT"
    COMPLETED = "COMPLETED"

    STATUS_CHOICE = [
        (TO_DO, "PENDING"),
        (ON_IT, "ON IT"),
        (COMPLETED, "COMPLETED")
    ]
    task = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, verbose_name = "Task Name")
    collaborator = models.ManyToManyField(Invitation, related_name='subtasks', verbose_name='Assign To', blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICE, default=TO_DO)
    due_date = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        if self.task:
            return f"{self.name} for {self.task.name}"
        else:
            return f"{self.name} (No Task Assigned)"
        
    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        return super().save(*args, **kwargs)

    
class ToDOList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name = "Task Name")
    completed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.name 
    
    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        return super().save(*args, **kwargs)

    
