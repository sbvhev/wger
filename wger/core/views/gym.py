# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseForbidden
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import ListView
from django.views.generic import DeleteView
from django.views.generic import CreateView
from django.views.generic import UpdateView

from wger.core.forms import GymUserAddForm
from wger.core.models import Gym
from wger.utils.generic_views import WgerFormMixin
from wger.utils.generic_views import WgerDeleteMixin
from wger.utils.generic_views import WgerPermissionMixin
from wger.utils.helpers import password_generator


logger = logging.getLogger('wger.custom')


class GymListView(WgerPermissionMixin, ListView):
    '''
    Overview of all available gyms
    '''
    model = Gym
    permission_required = 'core.manage_gyms'
    template_name = 'gym/list.html'


class GymUserListView(WgerPermissionMixin, ListView):
    '''
    Overview of all users for a specific gym
    '''
    model = User
    permission_required = ('core.manage_gym', 'core.gym_trainer')
    template_name = 'gym/member_list.html'

    def dispatch(self, request, *args, **kwargs):
        '''
        Only managers and trainers for this gym can access the members
        '''
        if (request.user.has_perm('core.manage_gym') or request.user.has_perm('core.gym_trainer')) \
                and request.user.userprofile.gym_id == int(self.kwargs['pk']):
            return super(GymUserListView, self).dispatch(request, *args, **kwargs)
        return HttpResponseForbidden()

    def get_queryset(self):
        '''
        Return a list with the users, not really a queryset.
        '''
        out = []
        for u in User.objects.filter(userprofile__gym_id=self.kwargs['pk']):
            out.append({'obj': u,
                        'perms': {'manage_gym': u.has_perm('core.manage_gym'),
                                  'manage_gyms': u.has_perm('core.manage_gyms'),
                                  'gym_trainer': u.has_perm('core.gym_trainer'),
                                  'any_admin': u.has_perm('core.manage_gym')
                                               or u.has_perm('core.manage_gyms')
                                               or u.has_perm('core.gym_trainer')}})
        return out

    def get_context_data(self, **kwargs):
        '''
        Pass other info to the template
        '''
        context = super(GymUserListView, self).get_context_data(**kwargs)
        context['gym'] = Gym.objects.get(pk=self.kwargs['pk'])
        context['admin_count'] = len([i for i in context['object_list'] if i['perms']['any_admin']])
        context['user_count'] = len([i for i in context['object_list'] if not i['perms']['any_admin']])
        return context


class GymAddView(WgerFormMixin, CreateView):
    '''
    View to add a new gym
    '''

    model = Gym
    success_url = reverse_lazy('core:gym-list')
    title = ugettext_lazy('Add gym')
    form_action = reverse_lazy('core:gym-add')
    permission_required = 'core.add_gym'


@login_required
def gym_new_user_info(request):
    '''
    Shows info about a newly created user
    '''
    if not (request.user.has_perm('core.manage_gym') or request.user.has_perm('core.manage_gym')):
        return HttpResponseForbidden()

    context = {'new_user': User.objects.get(pk=request.session['gym.user']['user_pk']),
               'password': request.session['gym.user']['password']}
    return render(request, 'gym/new_user.html', context)


class GymAddUserView(WgerFormMixin, CreateView):
    '''
    View to add a user to a new gym
    '''

    model = User
    title = ugettext_lazy('Add user to gym')
    success_url = reverse_lazy('core:gym-new-user-data')
    permission_required = 'core.manage_gym'
    form_class = GymUserAddForm

    def dispatch(self, request, *args, **kwargs):
        '''
        Only managers for this gym can add new members
        '''
        if not request.user.is_authenticated():
            return HttpResponseForbidden()

        gym_id = request.user.userprofile.gym_id
        if request.user.has_perm('core.manage_gym') and gym_id == int(self.kwargs['gym_pk']):
            return super(GymAddUserView, self).dispatch(request, *args, **kwargs)
        return HttpResponseForbidden()

    def form_valid(self, form):
        '''
        Create the user, set the user permissions and gym
        '''
        gym = Gym.objects.get(pk=self.kwargs['gym_pk'])
        password = password_generator()
        user = User.objects.create_user(form.cleaned_data['username'],
                                        form.cleaned_data['email'],
                                        password)
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        form.instance = user

        user.userprofile.gym = gym
        user.userprofile.save()

        if form.cleaned_data['role'] != 'user':
            content_type = ContentType.objects.get_for_model(Gym)
            if form.cleaned_data['role'] == 'trainer':
                permission = Permission.objects.get(content_type=content_type,
                                                    codename='gym_trainer')
            elif form.cleaned_data['role'] == 'admin':
                permission = Permission.objects.get(content_type=content_type,
                                                    codename='manage_gym')
            user.user_permissions.add(permission)

        self.request.session['gym.user'] = {'user_pk': user.pk,
                                            'password': password}

        return super(GymAddUserView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(GymAddUserView, self).get_context_data(**kwargs)
        context['form_action'] = reverse('core:gym-add-user',
                                         kwargs={'gym_pk': self.kwargs['gym_pk']})
        return context


class GymUpdateView(WgerFormMixin, UpdateView):
    '''
    View to update an existing license
    '''

    model = Gym
    title = ugettext_lazy('Edit gym')
    permission_required = 'core.change_gym'

    def get_context_data(self, **kwargs):
        '''
        Send some additional data to the template
        '''
        context = super(GymUpdateView, self).get_context_data(**kwargs)
        context['form_action'] = reverse('core:gym-edit', kwargs={'pk': self.object.id})
        context['title'] = _(u'Edit {0}'.format(self.object))
        return context


class GymDeleteView(WgerDeleteMixin, DeleteView, WgerPermissionMixin):
    '''
    View to delete an existing gym
    '''

    model = Gym
    success_url = reverse_lazy('core:gym-list')
    permission_required = 'core.delete_gym'

    def get_context_data(self, **kwargs):
        '''
        Send some additional data to the template
        '''
        context = super(GymDeleteView, self).get_context_data(**kwargs)
        context['title'] = _(u'Delete {0}?'.format(self.object))
        context['form_action'] = reverse('core:gym-delete', kwargs={'pk': self.kwargs['pk']})
        return context
