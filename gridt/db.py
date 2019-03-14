'''
db Module
*********

This module provides the application level database. To add objects to the
send models to the database use the following piece of code: ::

    from gridt.db import db
    db.session.add(your_model)
    db.session.commit()

    # Or if you want to commit multipe_models
    db.session.add_all(list_of_models)
    db.session.commit()


For more information on the use of db read the `flask sqlalchemy docs <http://flask-sqlalchemy.pocoo.org/>`_.

'''

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
