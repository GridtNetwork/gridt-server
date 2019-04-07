import os
from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock
from flask import Config

from gridt.app import create_app


def spy_decorator(method_to_decorate):
    mock = MagicMock()

    def wrapper(self, *args, **kwargs):
        mock(*args, **kwargs)
        return method_to_decorate(self, *args, **kwargs)

    wrapper.mock = mock
    return wrapper


class AppTest(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_open(self):
        self.fs.create_file("test", contents="Hello!")
        with open("test") as f:
            f.read()

    def test_overwrite_conf(self):
        self.fs.create_file(
            "/gridt/conf/test_conf.conf",
            contents="SECRET_KEY='test'\nSQLALCHEMY_DATABASE_URI='sqlite://'",
        )
        spy = spy_decorator(Config.from_pyfile)
        with patch.object(Config, "from_pyfile", spy):
            app = create_app("/gridt/conf/test_conf.conf")
        spy.mock.assert_called_with("/gridt/conf/test_conf.conf")

    def test_from_terminal_conf(self):
        self.fs.create_file(
            "/conf/my_test.conf",
            contents="SECRET_KEY='test'\nSQLALCHEMY_DATABASE_URI='sqlite://'",
        )
        with patch.dict("os.environ", {"FLASK_CONFIGURATION": "/conf/my_test.conf"}):
            spy = spy_decorator(Config.from_pyfile)
            with patch.object(Config, "from_pyfile", spy):
                app = create_app()
            spy.mock.assert_called_with("/conf/my_test.conf")
            spy.mock.assert_called()

    def test_conf(self):
        self.fs.pause()
        self.fs.create_file(
            os.getcwd() + "/gridt/conf/default.conf",
            contents="SECRET_KEY='test'\nSQLALCHEMY_DATABASE_URI='sqlite://'",
        )
        self.fs.resume()
        spy = spy_decorator(Config.from_pyfile)
        with patch.object(Config, "from_pyfile", spy):
            app = create_app()
        spy.mock.assert_called_with("conf/default.conf")
