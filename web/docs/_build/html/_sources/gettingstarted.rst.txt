Getting Started
***************

=======
Cloning
=======
To start developing gridt download it::

   $ git clone https://github.com/GridtNetwork/grid-server

Now you are ready to start developing!

=================
Running all tests
=================
Make sure you are in ``gridt-server/gridt`` and run::

   $ python -m unittest

=========================
Initializing the database
=========================
To be able to run the database, you first have to initialize the database. This can be done by running the following command: ::

   $ flask initdb

This will create a file called gridt.db in the gridt/ folder, with the correct tables ready to be filled with data.

==================
Creating test data
==================
To generate test data run: ::

   $ flask insert-test-data
