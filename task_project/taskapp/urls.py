from django.urls import path
from taskapp import views

app_name = 'taskapp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('register/', views.regiter, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-project/', views.add_project, name='add_project'),
    path('collaborations/', views.collaboration_view, name='collaboration_view'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('activate-collaborator/<uidb64>/<token>', views.activate_collaborator, name='activate_collaborator'),
    path('delete_task/<int:task_id>', views.delete_task, name='delete_task'),
    path('update-task/<int:task_id>/', views.update_task_completion, name='update_task_completion'),
    path('collaboration-details/<int:project_id>/', views.collaboration_details, name='collaboration_details'),

]