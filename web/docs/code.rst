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
Configuration files for the gridt network can be set using the
``FLASK_CONFIGURATION`` environment variable. Using this variable the default
settings can be changed.

.. code-block:: bash

   $ export FLASK_CONFIGURATION=/path/to/your/configuration/file.conf

Here is where you can set the SECRET_KEY and any other configuration setting
you would like to use.

Secret keys
-----------
There is two possible ways to set the secret key of your project: trough the
normal setting of ``SECRET_KEY`` in the conf file, or by setting the
``SECRET_KEY_FILE``. This string should be a path to a file containing only one
line. If a secret key is specified the secret key file will be ignoren. Note
that if neither are present, or if the file is empty or if it has more than one
line, the application will not start.

Database URI
------------
In a similar vein, ``SQLALCHEMY_DATABASE_URI`` (for more details on this visit the
`sql alchemy documentation <https://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine>`_
can be set in two ways, either simply by setting it in the conf file or by
constructing it with:

   - DB_DIALECT (required)
   - DB_DRIVER
   - DB_USER (required)
   - DB_PASSWORD (required)
   - DB_HOST (required)
