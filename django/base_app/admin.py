from django.contrib import admin
from .models import *
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from base_app.models.app_configurations import CONFIGURATION_DEFINITIONS


@admin.register(AppConfiguration)
class AppConfiguration(admin.ModelAdmin):
    form = DynamicAppConfigurationForm

    readonly_fields = ['display_name', 'setting_description']
    fields = ('display_name', 'setting_description', 'value')
    list_display = ('setting_name', 'value')
    change_form_template = 'entities/app_configuration_changeform.html'

    # Change display name to show as name
    def setting_name(self, obj):
        return obj.display_name

    setting_name.short_description = 'name'

    def setting_description(self, obj):
        return obj.description

    setting_description.short_description = 'description'

    # Settings are created and deleted when the app starts,
    # so creation and deletion are forbidden during runtime
    def has_delete_permission(self, request, obj=None):
        """
        Prevents users from deleting settings in the django admin
        """
        return False

    def has_add_permission(self, request, obj=None):
        """
        Prevents users from adding settings in the django admin
        """
        return False

    def response_change(self, request, obj):
        if "_reset-default" in request.POST:
            obj.value = CONFIGURATION_DEFINITIONS[obj.name].default_value
            obj.save()
            self.message_user(
                request,
                _('The setting has been reset to its default value successfully')
            )
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """ Admin page for tokens. """

    # The random string is not editable,
    # it changes when the user clicks the regenerate button.
    readonly_fields = ['token']

    fields = ['client_name', 'token_type']
    list_display = ['client_name', 'token', 'token_type']

    def save_model(self, request, obj, form, change):
        """ Method override: creates the random string in the token. """
        super().save_model(request, obj, form, change)
        obj.regenerate_token()
