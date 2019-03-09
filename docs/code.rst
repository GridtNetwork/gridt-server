Documentation
*************

Gridt Package
=============

This module contains the entire gridt-server and suffices to run the app. To
run the app edit the file `gridt/conf/default.conf` and replace the secret key.
Then run in your terminal::

    $ flask run

which will run your development server. This will grab :func:`create_app`

.. automodule:: app
   :members:
   :show-inheritance:

Conf files
==========
In the conf directory you will be able to edit the configuration files. Select
the configuration file by choosing one of three: default, development or
testing. To make the app read your configuration set it trough:

.. code-block:: bash

   $ export FLASK_CONFIGURATION=<default|development|testing>

Here is where you can set the SECRET_KEY, or any other configuration setting
you would like to use.
