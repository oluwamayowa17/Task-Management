from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomAccountManager(BaseUserManager):
    def create_superuser(self, email, user_name, password, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must be assigned to is_staff=True'
            )
        if other_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must be assigned to is_superuser=True'
            )
        
        return self.create_user(email, user_name, password, **other_fields)

    def  create_user(self, email, user_name, password, **other_fields):
        if not email:
            raise ValueError(_('You must provide an email address'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, **other_fields)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(_('Email Address'), unique=True)
    user_name = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=150, blank=True)

    #user status
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_collaborator = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)   

    objects = CustomAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name', ]

    class Meta():
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.user_name
    
    def is_project_user(self):
        """
        Method to determine the project user role.
        """
        if self.is_staff and self.is_superuser:
            return "Administrator"
        elif self.is_staff:
            return "Project Leader"
        elif self.is_collaborator:
            return "Collaborator"
        else:
            return "Regular User"
    

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
    due_date = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.name 
    
    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        return super().save(*args, **kwargs)
    
class Collaborator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'project', )

    def __str__(self):
        if self.email:
            return self.email
        else:
            return "No Email Assigned"


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
    assignees = models.ManyToManyField(Collaborator, related_name='subtasks', verbose_name='Assign To', blank=True)
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

    
