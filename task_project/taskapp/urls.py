from django.urls import path
from taskapp import views

app_name = 'taskapp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('all-projects/', views.project_view, name='project'),
    path('add-project/', views.add_project, name='add_project'),
    path('collaborations/', views.collaboration_view, name='collaboration_view'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('delete_task/<int:task_id>', views.delete_task, name='delete_task'),
    path('update-task/<int:task_id>/', views.update_task_completion, name='update_task_completion'),
    path('collaboration-details/<int:project_id>/', views.collaboration_details, name='collaboration_details'),

]