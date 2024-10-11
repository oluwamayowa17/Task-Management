from django.contrib import admin
from .models import Project, ToDOList, SubTask, Collaborator, Invitation
# Register your models here.


admin.site.register(Project)
admin.site.register(SubTask)
admin.site.register(ToDOList)
admin.site.register(Collaborator)
admin.site.register(Invitation)