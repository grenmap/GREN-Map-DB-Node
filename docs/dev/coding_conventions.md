# Coding Conventions Guidelines

## HTML/Django Templates

- HTML5
- element IDs: hyphenated-names, e.g. "my-element-id"
- CSS classes: hyphenated-names, e.g"a-custom-class"
- 4-space indents ("soft tabs" i.e. spaces, not hard tab characters)
- double-indent element start tag line continuations
- 100-char lines, but somewhat flexible where it’s inconvenient (ex. to chain elements together without whitespace introduction)
- indent returns to 0 for each template file, makinno assumptions about where the indent would
  be in the final HTML output

## CSS

- 4-space indents ("soft tabs" i.e. spaces, not hardtab characters)
- Less is used for styling
- classes: hyphenated-names, e.g. "a-custom-class"

## Python

[PEP8](https://www.python.org/dev/peps/pep-0008/) except where noted below.

 - 99-char lines, except:
     * Docstrings (72 chars from column 0)
     * don't break long URLs in comments
     * translated strings, for better compatibility with makemessages
     * Markdown documentation files (unlimited)
 - 4-space indents ("soft tabs" i.e. spaces, not hard tab characters)
 - double-indent line continuations
 - indented blocks usually preferred over line continuations
 - Python objects destined for output to JSON may use either underscore_delimited properties or hyphen-delimited properties; ideally, they're the former in Python and then run through a simple translation function prior to output to a client via JSON
 - do not capitalize acronyms & abbreviations in variables, properties, attributes, arguments, parameters; capitalize them in class names, e.g.:
   * my_id = ID(name='Joe', pin=encode('1234'))

Prioritize readability over dogmatic adherence to conventions.  Where exceptions are warranted, mark lines with flake8 `# noqa` comments targeting the specific rule being ignored.

To check the code against established conventions during development, run the following command:
  ```
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T app flake8 .
  ```

To check the code against established conventions directly on the codebase (without a running app container):
  ```
  cd django
  flake8 --config setup.cfg
  ```

## UI Style

 - large tables should implement independent scrolling
 - all public pages should be suitably functional on mobile devices as small as a smartphone
 - WCAG accessibility should be considered and is strongly recommended for all external UIs
 - use \<button> instead of \<input type=”button” />; IE6 is dead

## Language

 - all code should be crafted in English
 - log/debugging code, API status/error messages, and other internal- or dev-only strings should
   be in English

## Logging

 - Use Python for server-side messages and errors
 - New apps should register their logging handler in settings/base.py, then use it
 - Logs should all go out to the standard output to be handled by the logging framework(see [Logging](logging.md) )


## Settings

There are two locations for plugin/app settings:

 1. in the ORM database as GRENSetting objects: the recommended way to implement configuration
 2. in the "settings" package of the GREN app, a legacy mechanism based on the built-in Django configuration paradigm

The first should be the default for any new configuration items, with the former being used only for core features that are likely to change extremely rarely in production and/or may present a weaker security profile if located in the database.

When changing Python-based settings, base.py is checked in to source control and will be deployed to all instances; change it with great care.  local.py and development.py are equivalent files that will add to or override the core settings in base.py.  local.py is intended for instance-specific configuration.  development.py is for overriding both of the above during development, for example, temporarily whitelisting a direct-login user by appending to DIRECT_LOGIN_ALLOWED_USERS.  An example of how to populate these files is contained in local.dev.py.example in the same directory.

Neither of the latter two files (local.py and development.py) are checked into source control, for two reasons:

 1. they are intended to be unique to each instance, and
 2. they are likely to contain "secrets".

For more, see [Configuration](../admin/configuration.md)

## Migrations

(It is possible that recent versions of Django have obviated the need for the below.)

Deleted or renamed models might prompt for messages during deployment. However, deployment should be able to run unattended (ie. Jenkins). Thus, when models are removed or renamed, there is Python code to be placed in the migration file that will take care of it explicitly without prompting:

```python
from __future__ import unicode_literals
from django.db import models, migrations
from django.contrib.contenttypes.models import ContentType

DEL_MODELS_0008 = ['member']

def _remove_content_types(apps, schema_editor):
    ct = ContentType.objects.all()
    for c in ct:
        if (c.model in DEL_MODELS_0008):
        c.delete()

def _reverse_remove_content_types(apps, schema_editor):
    pass # restore the ContentType if possible (...but, do we need to?)

class Migration(migrations.Migration):

    dependencies = [ … ]

    operations = [
        migrations.RunPython(_remove_content_types, _reverse_remove_content_types),
        …
    ]
```

# General Development Tips

## Debugging Mode

It is recommended to develop using the setting DEBUG = True, as, among other things, this will pass server-side errors through the HTTP request to the client.  The docker-compose.dev.yml file as shipped sets this.

If a 500 server error is given from an endpoint while performing development, the browser will display the stack trace for the error that was raised while DEBUG is set to true. Because of this, it is imperative to have DEBUG set to false for production instances
