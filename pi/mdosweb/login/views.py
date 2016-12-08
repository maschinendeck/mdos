from django.shortcuts import render
from django import forms
from django.views.generic import TemplateView, FormView, View
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from serialdoorconnection import startSession, finishSession, closeDoor, setRoomState
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

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
        return render(request, self.template_name, {'form': form})

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            if form.cleaned_data['session'] == '':
                try:
                    if form.cleaned_data['action'] == 'close':
                        closeDoor()
                    else:
                        startSession()
                        form = self.form_class(initial={'session': 'dummy'})
                except Exception, e:
                    messages.error(self.request, e)
            else:
                
                try:
                    finishSession(form.cleaned_data['pin'])
                    messages.info(self.request, "Door opened.")
                except Exception, e:
                    messages.error(self.request, e)
                return HttpResponseRedirect(self.success_url)
                
        return render(request, self.template_name, {'form': form})
    
@method_decorator(csrf_exempt, name='dispatch')
class RoomStateView(View):
    def post(self, request, *args, **kwargs):
        if request.POST.get('state') == 'open':
            setRoomState(True)
        else:
            setRoomState(False)
        return HttpResponse(status=200)

