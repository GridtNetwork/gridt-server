import os
from unittest import TestCase
from unittest.mock import patch
from flask import Config

from gridt.app import create_app


class AppTest(TestCase):
    def test_overwrite_conf(self):
        with patch.object(Config, "from_pyfile", return_value=None) as mocked_fun:
            app = create_app("test_conf")
            mocked_fun.assert_called_with(os.getcwd() + "/gridt/conf/test_conf.conf")
