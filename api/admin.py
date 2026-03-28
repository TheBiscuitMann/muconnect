from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department, Student, Faculty, Course, Enrollment, Result, Notice


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role']
    list_filter  = ['role']
    fieldsets    = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


admin.site.register(Department)
admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Result)
admin.site.register(Notice)