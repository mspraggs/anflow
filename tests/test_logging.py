from __future__ import absolute_import

import pytest

from anflow.logging import logger



class TestLogging(object):

    def test_logger(self):
        """Test the logger function"""

        def some_function():
            log = logger()
            return log

        class SomeClass(object):
            def blah(self):
                return logger()

        function_log = some_function()
        assert function_log.name == "tests.test_logging.some_function"
        instance = SomeClass()
        class_log = instance.blah()
        assert class_log.name == "tests.test_logging.SomeClass.blah"
