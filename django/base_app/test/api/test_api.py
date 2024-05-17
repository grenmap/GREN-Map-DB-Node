"""
This is an example file for writing unit tests.
TODO: Get manage.py to detect the files in this directory

To run tests automatically upon docker build, you can add python
manage.py test to wait_for_db.sh
"""


from django.http import HttpRequest
from base_app.views.api import status_api


class TestSampleAPI:

    def test_status_api(self):
        request = HttpRequest()
        request.method = 'GET'
        response = status_api(request)
        assert response.status_code == 200, 'Test API did not return successful status code'
