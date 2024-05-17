# GREN Map Internationalization

Currently the display language is selected from the available options based on the language settings in the users browser; this cannot be overridden manually.

## Django Translation Mechanism

Django has an official built-in translation mechanism that allows text to be displayed to the user to be translated into the user's current preferred language. For more complete details on how the this works please consult the [official Django documentation](https://docs.djangoproject.com/en/3.2/topics/i18n/translation/).

The built-in Django Admin interface has already been translated for the majority of languages.  Strings specific to the project, including custom Django Admin interface elements, should be carefully marked for translation.  The actual translation of the text may be done immediately or left for future work by interested parties.  For development purposes English is the required default language.

## Adding User-Facing Strings

When adding text that users may see, the following mechanism and wrapper function should be used in Python code:

```python
from django.utils.translation import gettext as _

# in the code...
output = \_('Text to be translated')
```

This wrapper function indicates to Django that the string should be picked up by the translation mechanism.

If you are using a constant in the code it will be evaluated when Django starts up. Use `gettext_lazy` to translate the constant's value.

```python
from django.utils.translation import gettext_lazy as _lazy

MY_CONSTANT = _lazy('special value')

# in the code...
built_string = 'Special Value: ' + MY_CONSTANT
```

All strings should be written in English as a default.

### Templates and Javascript

Please see the [official Django documentation](https://docs.djangoproject.com/en/3.2/topics/i18n/translation/) for details on how to configure with templates and javascript when required.

## Preparing the Translation Matrix

In order to provide translations for a particular language, a special text file needs to be generated for each app so that appropriate alternative text can be supplied for each of the strings identified in the code as shown above.

Django provides a function called makemessages in the manage.py tool. This will need to be called in the following cases:
* A new string is added to the code.
* A string's content is updated.
* Translations for a new language are required.

This is a manual step.  Beware: it will recreate the translation files with a new date even if they have not changed.

To run makemessages for a specific language the following command can be used (in this case for French):

    python manage.py makemessages -l fr

To run in the Django Docker container that contains the correct context the following command can be used:

```bash
# from the root dir of the gren-map-db-node
docker container run \
--env-file=./env/.env.dev \
--volume=`pwd`/django:/home/grenmapadmin/web \
--entrypoint=/bin/sh \
gren-map-db-node_prod -c 'python manage.py makemessages -l fr'
```

Where _gren-map-db-node_prod_ is the name of the Docker container on your system. This will just run the Django container and call this method. As the code is shared as a volume the translation files will be created in the correct place. Depending on your host operating system you may need to look at file permissions.

If the composed set of containers is already running, a command like the following can be used:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml \
exec -T app python manage.py makemessages -l fr
```

Each language needs to be specified individually. Note, there is a --all switch but it will *not* create new language files if needed, only update existing ones.

A convenience script has been written that will dynamically pick up all of the languages defined in the Django settings and create files for them.

```bash
#from the root dir of the gren-map-db-node
docker container run \
--env-file=./env/.env.dev \
--volume=`pwd`/django:/home/grenmapadmin/web \
--entrypoint=/bin/sh \
gren-map-db-node_prod -c './process_all_locales.py'
```

This will generate .po files in the `/locale` subdirectory of each Django app. These can then have translation strings added for the appropriate language.

## Updating the Translation Matrix

Insert the translated strings into the .po file under its English placeholder string.  Take great care to respect exact formatting.

### Examples:

Single-line:
```
#: my_app/views.py:13
msgid "This is eloquent prose."
msgstr "Esta é uma prosa eloquente."
```

Multi-line:
```
#: my_app/utils/error_messages.py:14
msgid ""
"First line, "
"second line."
msgstr ""
"Première ligne, "
"deuxième ligne"
```

## Compiling

Once the translations in the .po files have been filled in, these translation files are then compiled for actual use by the app.  This step is currently handled by the Docker container on startup.

### Process

The .po files in which we write translations are the input of the gettext compiler. The output are the .mo files. These are the files Django loads to obtain localized messages.

The commands below are useful during development. To run them, you can open a shell on the `app` container in your local GRENMap deployment: `docker exec -it gren-map-db-node_prod /bin/sh` or the equivalent Docker Compose command `docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T sh`.

```
# This compiles all French locale files:
python manage.py compilemessages -l fr

# This restarts the gunicorn process that responds to the HTTP requests,
# which will load the updated .mo files:
kill -HUP 1
```
