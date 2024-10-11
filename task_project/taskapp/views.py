from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.views.generic import TemplateView
from .forms import ToDOForm, ProjectForm, TaskForm
from .models import *
from collab.views import invite_collaborator
from django.db.models import Count, Q
from .token import collaborator_token
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import json



# Create your views here.

class IndexView(TemplateView):
    template_name = 'index.html'


@login_required(login_url='/login/')    
def dashboard(request):
    user = request.user  
    to_do_list = ToDOList.objects.filter(user=user)
    projects = Project.objects.filter(user=request.user).distinct().order_by('-created')[:5]
    all_projects = Project.objects.filter(user=request.user)
    pending = Project.objects.filter(user=request.user, status='PENDING')
    in_progress = Project.objects.filter(user=request.user, status='IN PROGRESS')
    completed = Project.objects.filter(user=request.user, status='COMPLETED')
    # Count collaborators for each project
    for project in projects:
        # project.num_collaborators = Project.objects.filter(collaborator=project).count()
        project.num_task = SubTask.objects.filter(task=project).count()
    
    if request.method == "POST":
        task = ToDOForm(request.POST)
        if task.is_valid():
            new_task = task.save(commit=False)
            new_task.user = user  # Associate the task with the current user
            new_task.save()
    else:
        task = ToDOForm()

    project_progress = []
    for project in projects:
        completed_tasks = SubTask.objects.filter(task__id=project.id, status='COMPLETED').count()
        total_tasks = SubTask.objects.filter(task__id=project.id).count()
        
        if total_tasks > 0:
            progress = (completed_tasks / total_tasks) * 100
        else:
            if project.status == 'COMPLETED':
                progress = 100     
            elif project.status == 'IN PROGRESS':
                progress = 50   
            else:
                progress = 0  
        project_progress.append({'project': project, 'progress': progress})
    context = {
        'task': task,
        'to_do_list': to_do_list,
        'projects':projects,
        'project_progress':project_progress,
        'all_project':all_projects,
        'pending':pending,
        'in_progress':in_progress,
        'completed':completed,
    }
    return render(request, 'dashboard.html', context)

def delete_task(request, task_id):
    task = get_object_or_404(ToDOList, id=task_id)
    task.delete()
    return redirect('taskapp:dashboard')

@require_POST
def update_task_completion(request, task_id):
    if request.method == 'POST':
        # Fetch the task from the database
        try:
            task = ToDOList.objects.get(pk=task_id)
        except ToDOList.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)

        # Parse the JSON data from the request body
        data = json.loads(request.body.decode('utf-8'))
        completed = data.get('completed')

        # Update the completion status based on the AJAX request data
        if completed is not None:
            task.completed = completed
            task.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid data'})

    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)  # Assuming you have a ProjectForm defined
        if form.is_valid():
            # Save the project instance from the form
            project = form.save(commit=False)  # Don't save to database yet

            project.user = request.user
        
            project.save()

            # Redirect to a success page or the page where the form was submitted
            return redirect('taskapp:dashboard')
    else:
        form = ProjectForm()  # Assuming you have a ProjectForm defined

    context = {
        'project': form,
    }
    return render(request, 'add_project.html', context)

def project_view(request):
    user = request.user
    projects = Project.objects.filter(user=user)
    context = {
        'projects':projects,
    }
    return render(request, 'projects.html', context)

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    subtasks = SubTask.objects.filter(task_id=project_id)
    task_form = TaskForm(project_id=project)
    task_form = TaskForm(request.POST, project_id=project)
    if task_form.is_valid():
        new_task = task_form.save(commit=False)
        new_task.user = request.user
        new_task.task = project
        new_task.save()
        task_form.save_m2m()
        messages.success(request, 'Task successfully assigned to collaborator.')
    email = request.POST.get('email')
    invite_collaborator(request, email, project, project_id)  
    if request.method == 'POST':
        # Update the project status
        if project.status == 'PENDING':
            project.status = 'IN PROGRESS'
            project.save()
            messages.success(request, 'Project started successfully!')
       
    context = {
        'detail': project,
        'subtask': subtasks,
        'task': task_form,
    }
    return render(request, 'project-details.html', context)




def collaboration_view(request):
    invited_projects = Invitation.objects.filter(collaborator=request.user.email).values_list('project', flat=True)

    projects = Project.objects.filter(id__in=invited_projects)

    # Get the number of tasks assigned to the collaborator
    projects = projects.annotate(num_tasks=Count('subtask', filter=Q(subtask__collaborator__collaborator=request.user.email)))


    context = {
        'projects': projects,
        'collaborations': invited_projects,
    }
    return render(request, 'collaboration.html', context)

def collaboration_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    collaborator_email = request.user.email  # Assuming the collaborator's email is stored in the User model

    # Retrieve subtasks assigned to the collaborator for the specified project
    assigned_tasks = SubTask.objects.filter(collaborator__collaborator=collaborator_email, task=project)

    context = {
        'detail':project,
        'assigned_tasks': assigned_tasks,
    }
    return render(request, 'collaboration-details.html', context)

