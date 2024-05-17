
class CustomConfiguration:
    """
    Any configurations should extend this class or instantiate it
    to define custom app configuration settings
    """
    name = ''
    display_name = ''
    default_value = ''
    description = ''

    def clean(self, value):
        """
        Override this function to provide custom validation
        """
        pass

    def post_save(self, value):
        """
        Override this function to execute custom code when the setting
        is saved
        """
        pass
