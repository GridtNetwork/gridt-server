import os
from unittest import TestCase
from unittest.mock import patch
from flask import Config

from util.nostderr import nostderr
from gridt_server.app import create_app


class AppTest(TestCase):
    @patch.object(Config, "from_pyfile")
    def test_overwrite_conf(self, mocked_fun):
        with nostderr():
            with self.assertRaises(SystemExit):
                create_app("test_conf")
                mocked_fun.assert_called_with(
                    os.getcwd() + "/gridt/conf/test_conf.conf"
                )
