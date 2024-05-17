# Custom App Settings

Each app has the ability to define its own settings that will appear in the master list of settings. When settings are created, they cannot be deleted via the admin UI, only set to a new value or reset. Settings are defined using a single file that defines the settings validators, defaults and save hooks. Each setting must have at least the setting id, display name and default value to define what value the setting will have on the initial deploy of the application.  All settings are represented as string values, therefore any integer values may need to be converted before being used in the application. If the setting is removed from the apps settings definitions, it will be removed when the application is started.

## Configuration Definitions

Every app that wishes to define settings must define the settings it needs in a module called "app_configurations". The module only needs to contain classes extending CustomConfiguration representing the available settings for the app.

Example:
```python
class CustomSetting(CustomConfiguration):

    name = 'SETTING_NAME'
    display_name = 'Custom setting'
    default_value = 'test'
```

## Setting Validators

Every setting that wishes to validate its value must override the validator function.  The validator function accepts a single value, which is the setting value being validated. The validator is expected to return an empty string if the setting was successfully validated, or an error message describing why the setting was declined. The validator must take the following format:
```python
def clean(self, value):
    if value == 'invalid value':
        raise forms.ValidationError(
            _('The value provided was invalid'),
            code='invalid',
        )
```

## Setting Post Save Hooks

Each setting may define a save hook to execute after the object completes saving. This code may be used to keep remote services synchronised with the changed setting values or perform other operations that rely on the setting.  The save hook must take the following format:
```python
def post_save(self, value):
    # Do something
    pass
```
