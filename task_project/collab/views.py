from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.html import strip_tags
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, BadHeaderError
from taskapp.models import *
from django.contrib import messages

# Create your views here.



def invite_collaborator(request, email, project, project_id):
    if email:
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.is_active = True 
            user.save()

        existing_collaborator = Invitation.objects.filter(collaborator=email, project=project).first()
        if existing_collaborator:
            messages.error(request, f'A collaborator with the email {email} already exists for this project.')
            return redirect('taskapp:project_detail', project_id=project_id)

    
        # Create the project link with a secure token
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # Encode the user ID
        token = urlsafe_base64_encode(force_bytes(project_id))  # Encode the project ID
        
        project_link = request.build_absolute_uri(
            reverse('collab:accept-invitation', kwargs={'uidb64': uid, 'token': token})
        )
        # project_link = request.build_absolute_uri(reverse('taskapp:project_detail', kwargs={'project_id': project_id}))
        mail_subject = f"T.A.S.X.Y: You've been added as a collaborator to project: {project.name}"
        mail_context = {
            'domain': get_current_site(request).domain,
            'protocol': "https" if request.is_secure() else "http",
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

            Invitation.objects.create(collaborator=email, project=project)
            Collaborator.objects.get_or_create(user=user)

            messages.success(request, 'Invite sent and collaborator added!')
        except (BadHeaderError, Exception) as e:
            messages.error(request, f'Could not invite collaborator: {str(e)}')
        
        return redirect('taskapp:project_detail', project_id=project_id)


def accept_invitation(request, uidb64, token):
    try:
        # Decode the user and project IDs from the URL
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_object_or_404(User, pk=uid)

        project_id = urlsafe_base64_decode(token).decode()
        invitation = get_object_or_404(Invitation, collaborator=user.email, project_id=project_id)
        
        invitation.accepted = True
        invitation.save()

        messages.success(request, 'You have successfully accepted the invitation.')
        return redirect('taskapp:project_detail', project_id=project_id) 
    except (TypeError, ValueError, OverflowError, Invitation.DoesNotExist, User.DoesNotExist):
        messages.error(request, 'Invalid invitation link.')
        return redirect('/')