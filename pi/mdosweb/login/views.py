from django.shortcuts import render
from django import forms
from django.views.generic import TemplateView, FormView, View
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from serialdoorconnection import startSession, finishSession, closeDoor, setRoomState
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import LogEntry

def createLogEntry(request, action):
    log = LogEntry(user=request.user if request.user.is_authenticated else None, action=action, ip=request.META['REMOTE_ADDR'])
    log.save()

class OpenForm(forms.Form):
    pin = forms.CharField(widget=forms.TextInput, required=False)
    session = forms.CharField(widget=forms.HiddenInput, required=False)
    action = forms.CharField(widget=forms.HiddenInput, required=False)
    
    
class LoginView(View):
    template_name = "login.html"
    form_class = OpenForm
    success_url = '/login' #reverse('login') 

    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        createLogEntry(request, 'index')
        return render(request, self.template_name, {'form': form})

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            if form.cleaned_data['session'] == '':
                try:
                    if form.cleaned_data['action'] == 'close':
                        closeDoor()
                        createLogEntry(request, 'close')
                    else:
                        startSession()
                        createLogEntry(request, 'start_session')
                        form = self.form_class(initial={'session': 'dummy'})
                except Exception, e:
                    messages.error(self.request, e)
            else:
                
                try:
                    finishSession(form.cleaned_data['pin'])
                    createLogEntry(request, 'open')
                    messages.info(self.request, "Door opened.")
                except Exception, e:
                    createLogEntry(request, 'pin_fail')
                    messages.error(self.request, e)
                return HttpResponseRedirect(self.success_url)
                
        return render(request, self.template_name, {'form': form})
    
@method_decorator(csrf_exempt, name='dispatch')
class RoomStateView(View):
    def post(self, request, *args, **kwargs):
        if request.POST.get('state') == 'open':
            createLogEntry(request, 'roomstate_open')
            setRoomState(True)
        else:
            createLogEntry(request, 'roomstate_closed')
            setRoomState(False)
        return HttpResponse(status=200)

