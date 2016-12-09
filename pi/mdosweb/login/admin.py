from django.contrib import admin
from .models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return obj is None
    def has_add_permission(self, request, obj=None):
        return False
    

admin.site.register(LogEntry, LogEntryAdmin)
