# Program Logging

All containers should log their output to the standard stdout. This allows for different logging mechanisms to collect program logs in a consistent way.

## Python Logging

Developers should leverage Python's `logging` module.  Example:
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f'An fancy object with name {object_name} has been created.')
```

### Log Levels

Note the log level in the example above is "debug".  Debug messages are likely to be discarded in a production container.  Notable events in a GREN Map DB Node should have level "info".  Errors should use "error" or "exception" methods of the logger.  More [gradations](https://docs.python.org/3/library/logging.html#logging-levels) are available.
