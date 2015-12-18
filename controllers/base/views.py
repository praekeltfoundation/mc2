import json
import os.path

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import (
    login_required, user_passes_test)
from django.views.generic.base import View
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView, CreateView
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages

from organizations.utils import org_permission_required, active_organization

from controllers.base.models import Controller
from controllers.base.forms import ControllerForm
from controllers.base import exceptions

from unicoremc import tasks


@login_required
def update_marathon_exists_json(request, controller_pk):
    controller = get_object_or_404(Controller, pk=controller_pk)

    workflow = controller.get_builder().workflow
    if controller.state == 'done' and not controller.exists_on_marathon():
        workflow.take_action('missing')
        controller.save()
    elif controller.state == 'missing' and controller.exists_on_marathon():
        workflow.take_action('activate')
        controller.save()

    return HttpResponse(
        json.dumps({'state': controller.state}),
        content_type='application/json')


class ControllerViewMixin(View):
    pk_url_kwarg = 'controller_pk'
    permissions = []
    social_auth = None

    @classmethod
    def as_view(cls):
        view = super(ControllerViewMixin, cls).as_view()

        if cls.social_auth:
            view = user_passes_test(
                lambda u: u.social_auth.filter(
                    provider=cls.social_auth).exists(),
                login_url=reverse_lazy(
                    'social:begin', args=(cls.social_auth,)))(view)

        if cls.permissions:
            view = org_permission_required(cls.permissions)(view)

        return login_required(view)

    def dispatch(self, request, *args, **kwargs):
        return super(
            ControllerViewMixin, self).dispatch(request, *args, **kwargs)

    def get_controllers_queryset(self, request):
        organization = active_organization(request)
        if organization is None:
            if request.user.is_superuser:
                return Controller.objects.all()
            return Controller.objects.none()
        return Controller.objects.filter(organization=organization)


class ControllerCreateView(ControllerViewMixin, CreateView):
    form_class = ControllerForm
    template_name = 'controller_edit.html'
    permissions = ['controllers.base.add_controller']

    def get_success_url(self):
        return reverse("home")

    def form_valid(self, form):
        form.instance.organization = active_organization(self.request)
        form.instance.owner = self.request.user

        response = super(ControllerCreateView, self).form_valid(form)
        tasks.start_new_controller.delay(self.object.id)
        return response


class ControllerEditView(ControllerViewMixin, UpdateView):
    form_class = ControllerForm
    template_name = 'controller_edit.html'
    permissions = ['base.change_controller']

    def get_queryset(self):
        return self.get_controllers_queryset(self.request)

    def get_success_url(self):
        return reverse("home")

    def form_valid(self, form):
        response = super(ControllerEditView, self).form_valid(form)

        try:
            self.object.update_marathon_app()
        except exceptions.MarathonApiException:
            messages.error(
                self.request, 'Unable to update controller in marathon')
        return response


class AppLogView(ControllerViewMixin, TemplateView):
    template_name = 'app_logs.html'

    def get_context_data(self, *args, **kwargs):
        context = super(AppLogView, self).get_context_data(*args, **kwargs)
        controller = get_object_or_404(
            self.get_controllers_queryset(self.request),
            pk=kwargs['controller_pk'])
        tasks = controller.infra_manager.get_controller_marathon_tasks()
        context.update({
            'controller': controller,
            'tasks': tasks,
            'task_ids': [t['id'].split('.', 1)[1] for t in tasks],
            'scroll_backlog': (
                self.request.GET.get('n') or settings.LOGDRIVER_BACKLOG)
        })
        return context


class AppEventSourceView(ControllerViewMixin, View):

    def get(self, request, controller_pk, task_id, path):
        controller = get_object_or_404(
            self.get_controllers_queryset(request),
            pk=controller_pk)
        n = request.GET.get('n') or settings.LOGDRIVER_BACKLOG
        if path not in ['stdout', 'stderr']:
            return HttpResponseNotFound('File not found.')

        # NOTE: I'm piecing together the app_id and task_id here
        #       so as to not need to expose both in the templates.
        task = controller.infra_manager.get_controller_task_log_info(
            '%s.%s' % (controller.app_id, task_id))

        response = HttpResponse()
        response['X-Accel-Redirect'] = '%s?n=%s' % (os.path.join(
            settings.LOGDRIVER_PATH, task['task_host'],
            task['task_dir'], path), n)
        response['X-Accel-Buffering'] = 'no'
        return response


class ControllerRestartView(ControllerViewMixin, View):
    # TODO: Check user permissions

    def get(self, request, controller_pk):
        controller = get_object_or_404(Controller, pk=controller_pk)
        try:
            controller.marathon_restart_app()
            messages.info(self.request, 'App restart sent.')
        except exceptions.MarathonApiException:
            messages.error(
                self.request, 'App restart failed. Please try again.')
        return redirect('home')


class ControllerDeleteView(ControllerViewMixin, View):
    # TODO: Check user permissions

    def get(self, request, controller_pk):
        controller = get_object_or_404(Controller, pk=controller_pk)
        try:
            controller.delete()
            controller.marathon_destroy_app()
            messages.info(self.request, 'App deletion sent.')
        except exceptions.MarathonApiException:
            messages.error(
                self.request, 'Failed to delete app: %(id)s. Please try again.'
                              % {'id': controller.name}
            )
        return redirect('home')
