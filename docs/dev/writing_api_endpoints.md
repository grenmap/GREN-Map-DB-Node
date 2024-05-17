# Writing API Endpoints

For adding API end points to the Django container, the Django REST Framework is used.
Django REST Framework provides the ease of use, documentation, and adaptability that is needed for development and implementation of this application.

At a later date, the adaptability of Django REST Framework will allow for new modules to be installed for API creation and documentation. (Ex. Swagger)

To add an API end point to the Django container, go to <project_name>/views and either modify the api.py file or create a new file for your purpose.
Below is an example of a bare minimum API view to get started:

```python
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET', 'POST'])
def new_api(request):
    return Response()
```

Once you have your API endpoint created, navigate to the <project_name>/base_app/urls.py and add the following:

```python
<other imports>
from .views.<filename> import new_api

urlpatterns = [
    <other urls>,
    path('<url path>', new_api),
]
```

If any of your new endpoints should be part of GRENMap's public API, add it as an element of the `PUBLIC_API_ENDPOINTS` list in the base_app.schema module.

Start a server in your development environment and use the API docs link on the top right corner to open the Swagger UI page. Check that your new endpoints are documented correctly and that it is possible to call them from Swagger UI.

In case parameters are missing or incorrect, consider using `extend_schema` to decorate your endpoint handlers (the functions or methods in your api.py file). The first link below points to the decorator's online documentation. The second link points to its unit tests, which also serve as usage examples.

https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular.html#drf_spectacular.utils.extend_schema  
https://github.com/tfranzel/drf-spectacular/blob/master/tests/test_extend_schema.py

## REST API

When writing REST APIs for ORM model objects, often for testing purposes, it is advisable to consider a subclass of ModelViewSet.  The following is a complete REST API definition for a simple fictional model MyModel:

```python
# serializers module
class MyModelSerializer(ModelSerializer):
    pk = s.ReadOnlyField()

    class Meta:
        model = MyModel
        fields = '__all__'

# views module
class MyModelViewSet(ModelViewSet):
    """
    Standard REST CRUD API for MyModel.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [IsAuthenticated]

# urls module
router = DefaultRouter()
"""
The views produced by these ViewSets are intended strictly for
testing purposes and should not be used for any other purpose.
"""
router.register(r'my_models', api.MyModelViewSet)
urlpatterns = [
    path('my_app/test/', include(router.urls)),  # e.g. /my_app/test/my_models/
]
```
