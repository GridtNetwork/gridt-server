Documentation
*************

Gridt Package
=============

This module contains the entire gridt-server and suffices to run the app. To
run the app edit the file `gridt/conf/default.conf` and replace the secret key.
Then run in your terminal::

    $ flask run

which will run your development server. This will grab :func:`create_app`

.. automodule:: gridt.app
   :members:
   :show-inheritance:
.. automodule:: gridt.db
   :members:
   :show-inheritance:

Gridt command line application
==============================
Some functionality has been added to the ``$ flask`` command, beside the default values.
This is the output of ``$ flask --help``: ::

   Usage: flask [OPTIONS] COMMAND [ARGS]...

     A general utility script for Flask applications.

     Provides commands from Flask, extensions, and the application. Loads the
     application defined in the FLASK_APP environment variable, or from a
     wsgi.py file. Setting the FLASK_ENV environment variable to 'development'
     will enable debug mode.

       $ export FLASK_APP=hello.py
       $ export FLASK_ENV=development
       $ flask run

   Options:
     --version  Show the flask version
     --help     Show this message and exit.

   Commands:
     delete-movement   Delete a movement from the database.
     initdb            Initialize the database.
     insert-test-data  Insert test data into the database.
     routes            Show the routes for the app.
     run               Runs a development server.
     shell             Runs a shell in the app context.

Conf files
==========
In the conf directory you will be able to edit the configuration files. Select
the configuration file by choosing one of three: default, development or
testing. To make the app read your configuration set it trough:

.. code-block:: bash

   $ export FLASK_CONFIGURATION=<default|development|testing>

Here is where you can set the SECRET_KEY, or any other configuration setting
you would like to use.
