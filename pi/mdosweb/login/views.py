from django.shortcuts import render
from django import forms
from django.views.generic import TemplateView, FormView, View
from django.http import HttpResponseRedirect
from django.contrib import messages
import socket

class OpenForm(forms.Form):
    pin = forms.CharField(widget=forms.TextInput, required=False)
    session = forms.CharField(widget=forms.HiddenInput, required=False)
    

MDOS_IP = '127.0.0.1'
MDOS_PORT = 42002

    
class LoginView(View):
    template_name = "login.html"
    form_class = OpenForm
    success_url = '/login' #reverse('login')

    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((MDOS_IP, MDOS_PORT))

            if form.cleaned_data['session'] == '':
                s.send('start\n')
                sid = s.recv(1024)
                form = self.form_class(initial={'session': str(sid)})
                messages.info(self.request, 'start session')
            else:
                s.send('finish %s %04s\n' % (form.cleaned_data['session'], form.cleaned_data['pin']))
                res = s.recv(1)
                s.close()
                if res == '1':
                    messages.info(self.request, "Door is open!")
                else:
                    messages.error(self.request, "Error!")
                return HttpResponseRedirect(self.success_url)
            s.close()
                
        return render(request, self.template_name, {'form': form})
    
