from django.contrib import admin
from .models import User, Project, ToDOList, SubTask, Collaborator
# Register your models here.


admin.site.register(User)
admin.site.register(Project)
admin.site.register(SubTask)
admin.site.register(ToDOList)
admin.site.register(Collaborator)