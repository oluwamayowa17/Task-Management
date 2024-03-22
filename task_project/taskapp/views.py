from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .urls import *
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.views.generic import TemplateView
from .forms import RegistrationForm, LoginForm, ToDOForm, ProjectForm, TaskForm
from .models import *
from django.utils.safestring import mark_safe
from .token import account_activation_token

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
        user.save()

        messages.success(request, 'Thank you for email confirmaton, you can now login your account')
        return redirect('taskapp:user_login')
    else:
        messages.error(request, 'Activation link invalid!')

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

def dashboard(request):
    user = request.user  # Assuming request.user is authenticated
    to_do_list = ToDOList.objects.filter(user=user)
    # project = Project.objects.filter(user=user).order_by('-created')
    projects = Project.objects.annotate(num_subtasks=models.Count('subtask')).all()
    for project in projects:
        project.num_collaborators = Collaborator.objects.filter(project=project).count()

    if request.method == "POST":
        task = ToDOForm(request.POST)
        if task.is_valid():
            new_task = task.save(commit=False)
            new_task.user = user  # Associate the task with the current user
            new_task.save()
    else:
        task = ToDOForm()

    context = {
        'task': task,
        'to_do_list': to_do_list,
        'projects':projects,
        # 'collab':collab,
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
    if request.method == 'POST':
        # Handle task creation
        task_form = TaskForm(request.POST)
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
            project_link = request.build_absolute_uri(reverse('taskapp:project_detail', kwargs={'project_id': project_id}))
            mail_subject = f"T.A.S.X.Y: You've been added as a collaborator to project: {project.name}"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            html_message = render_to_string('collaborator-email-template.html', {'email': email, 'project_name': project.name, 'project_link': project_link})

            # plain_text = f"You've been added as a collaborator to project: {project.name}\n"
           
            plain_text =strip_tags(html_message)
            plain_text += f"Project URL: {project_link}" 
            try:
                existing_collaborator = Collaborator.objects.filter(email=email, project=project).first()
                if existing_collaborator:
                    messages.error(request, f'A collaborator with the email {email} already exists for this project.')
                    return redirect('taskapp:project_detail', project_id=project_id)

                email_message = EmailMessage(mail_subject, plain_text, from_email, to=recipient_list)
                email_message.send()
                
                Collaborator.objects.create(email=email, project=project)
                messages.success(request, 'Invite sent and collaborator added!')
            except (BadHeaderError, Exception) as e:
                messages.error(request, f'Could not invite collaborator: {str(e)}')

        return render(request, 'project-details.html', {'detail': project, 'subtask': subtasks, 'task': task_form})
    
    else:
        task_form = TaskForm()

    context={
        'detail': project,
        'subtask': subtasks,
        'task': task_form,
    }
    return render(request, 'project-details.html', context)



        




