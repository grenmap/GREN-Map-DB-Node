from django.contrib import admin
from fim.models import RSIdentity


@admin.register(RSIdentity)
class RSIdentity(admin.ModelAdmin):

    list_display = (
        'user',
        'eppn',
        'first_name',
        'last_name',
        'display_name',
        'email',
    )

    search_fields = ('eppn', 'email', 'first_name', 'last_name', 'display_name',)
    ordering = ('eppn',)

    readonly_fields = ['user']
