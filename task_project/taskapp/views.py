from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.views.generic import TemplateView
from .forms import RegistrationForm, LoginForm, ToDOForm, ProjectForm, TaskForm
from .models import *
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from .token import account_activation_token, collaborator_token

from django.utils.html import strip_tags
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, BadHeaderError
import json



# Create your views here.

class IndexView(TemplateView):
    template_name = 'index.html'

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_staff = True
        user.save()

        messages.success(request, 'Thank you for email confirmaton, you can now login your account')
        return redirect('taskapp:user_login')
    else:
        messages.error(request, 'Activation link invalid!')

    return redirect('/')

def activate_collaborator(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and collaborator_token.check_token(user, token):
        user.is_active = True
        user.save()
        # Redirect to dashboard or show a success message
        return HttpResponseRedirect(reverse_lazy('taskapp:user_login'))
    else:
        # Show an error message or redirect to home
        return redirect('/')

def activateEmail(request, user, to_email):
    mail_subject = 'Activate Your Account'
    mail_message = render_to_string('mail-template.html', {
        'user': user.user_name,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': "https" if request.is_secure() else "http"
    })
    email = EmailMessage(mail_subject, mail_message, to=[to_email])
    if email.send():
        message = mark_safe(
            f'Dear <b>{user}</b>, in order to complete registration, check your email @ <b>{to_email}</b>\
            and click on the activation link that was sent. <b>Note:</b> Check your spam folder.'
        )
        messages.success(request, message)
    else:
        message.error(request, f'Problem sending email to {to_email}, check if you typed it correctly')

def regiter(request):
    if request.method == "POST":
        register = RegistrationForm(request.POST)
        if register.is_valid():
            user = register.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, register.cleaned_data.get('email'))
        else:
            for error in list(register.errors.values()):
                messages.error(request, error)
    else:
        register = RegistrationForm()
    context = {'reg': register}
    return render(request, 'register.html', context)

def user_login(request):
    if request.method == "POST":
        user_log = LoginForm(request.POST)
        if user_log.is_valid():
            email = user_log.cleaned_data['email']
            password = user_log.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('taskapp:dashboard')
            else:
                messages.error(request, 'Email or password Incorrect')
    else:
        user_log = LoginForm()
    return render(request, 'login.html', {'login': user_log})

def user_logout(request):
    logout(request)
    return redirect('taskapp:user_login')

def dashboard(request):
    user = request.user  # Assuming request.user is authenticated
    to_do_list = ToDOList.objects.filter(user=user)
    projects = Project.objects.filter(user=request.user).distinct().order_by('-created')[:5]
    all_projects = projects.count()
    pending = Project.objects.filter(user=request.user, status='PENDING').count()
    in_progress = Project.objects.filter(user=request.user, status='IN PROGRESS').count()
    completed = Project.objects.filter(user=request.user, status='COMPLETED').count()
    # Count collaborators for each project
    for project in projects:
        project.num_collaborators = Collaborator.objects.filter(project=project).count()
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
        completed_tasks = SubTask.objects.filter(task_id=project.id, status='COMPLETED').count()
        total_tasks = SubTask.objects.filter(task_id=project.id).count()
        
        if total_tasks > 0:
            progress = (completed_tasks / total_tasks) * 100
        else:
            if project.status == 'COMPLETED':
                progress = 100  # If there are no total tasks and project status is completed, progress is 100%
            elif project.status == 'IN PROGRESS':
                progress = 50   # If there are no total tasks and project status is in progress, progress is 50%
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

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    subtasks = SubTask.objects.filter(task_id=project_id)
    task_form = TaskForm(user=request.user)

    # Handle task creation
    task_form = TaskForm(request.POST, user=request.user)
    if task_form.is_valid():
        new_task = task_form.save(commit=False)
        new_task.user = request.user
        new_task.task = project
        new_task.save()
        task_form.save_m2m()
        messages.success(request, 'Task successfully assigned to collaborator.')

    # Handle collaborator invitation
    email = request.POST.get('email')
    if email:
        # Check if the user with the provided email already exists
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.is_active = False  # Collaborator needs to activate their account
            user.save()

        # Check if the collaborator already exists for the project
        existing_collaborator = Collaborator.objects.filter(email=email, project=project).first()
        if existing_collaborator:
            messages.error(request, f'A collaborator with the email {email} already exists for this project.')
        else:
            # Collaborator does not exist, create new collaborator record and send invitation
            project_link = request.build_absolute_uri(reverse('taskapp:project_detail', kwargs={'project_id': project_id}))
            mail_subject = f"T.A.S.X.Y: You've been added as a collaborator to project: {project.name}"
            mail_context = {
                'domain': get_current_site(request).domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),  # Use project ID for token
                'token': collaborator_token.make_token(user),  # Use logged-in user for token
                'protocol': "https" if request.is_secure() else "http",
                'email': email,
                'project_name': project.name, 
                'project_link': project_link,
            }
            html_message = render_to_string('collaborator-email-template.html', mail_context)
            plain_text = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            try:
                email_message = EmailMessage(mail_subject, plain_text, from_email, to=recipient_list)
                email_message.send()
                Collaborator.objects.create(user=user, email=email, project=project)
                messages.success(request, 'Invite sent and collaborator added!')
            except (BadHeaderError, Exception) as e:
                messages.error(request, f'Could not invite collaborator: {str(e)}')

        return redirect('taskapp:project_detail', project_id=project_id)
    
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
from django.db.models import Count

def collaboration_view(request):
    user = request.user
    
    # Get all projects where the user is a collaborator
    collaborator_projects = Collaborator.objects.filter(user=user)

    # Fetch project details for the collaborator's projects
    projects = Project.objects.filter(id__in=collaborator_projects.values_list('project', flat=True))

    # Get the number of tasks assigned to the collaborator
    projects = projects.annotate(num_tasks=Count('subtask', filter=Q(subtask__assignees__in=collaborator_projects)))


    context = {
        'projects': projects,
        'collaborations': collaborator_projects,
    }

    return render(request, 'collaboration.html', context)

def collaboration_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    collaborator_email = request.user.email  # Assuming the collaborator's email is stored in the User model

    # Retrieve subtasks assigned to the collaborator for the specified project
    assigned_tasks = SubTask.objects.filter(assignees__email=collaborator_email, task=project)

    context = {
        'detail':project,
        'assigned_tasks': assigned_tasks,
    }
    return render(request, 'collaboration-details.html', context)

