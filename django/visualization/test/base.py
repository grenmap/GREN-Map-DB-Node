from graphene_django.utils.testing import GraphQLTestCase
from base_app.models import AppConfiguration
from visualization.app_configurations import (
    VisualizationEnabledSetting,
    VisualizationCachedSetting,
)


class BaseGraphQLTestCase(GraphQLTestCase):
    """
    Enables the setting for visualization prior to running the test
    """

    def __init__(self, *args, **kwargs):
        super(GraphQLTestCase, self).__init__(*args, **kwargs)

    def _enable_visualization(self):
        AppConfiguration.objects.create(
            name=VisualizationEnabledSetting.name,
            value=VisualizationEnabledSetting.default_value,
            display_name=VisualizationEnabledSetting.display_name
        )
        setting = AppConfiguration.objects.get(name='GREN_MAP_VISUALIZATION_ENABLED')
        setting.value = 'True'
        setting.save()

    def _enable_cache(self):
        AppConfiguration.objects.create(
            name=VisualizationCachedSetting.name,
            value=VisualizationCachedSetting.default_value,
            display_name=VisualizationCachedSetting.display_name
        )
        setting = AppConfiguration.objects.get(name=VisualizationCachedSetting.name)
        setting.value = 'True'
        setting.save()
