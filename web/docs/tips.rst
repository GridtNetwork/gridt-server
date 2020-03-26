Useful tips
***********

Calling db.session.commit() closes the session
==============================================
Imagine yourself writing a test for the a resource. First of all you instantiate the application context. Then you write some fake data to the database. You then make a request to the server that makes some changes to the server. Now you want to check if those changes were successful, you compare your previously instantiated models and you get a DetachedInstanceError.

This is because when the server closes the connection it closes the session as well. You will have to reinstantiate it by searching for your previously made data and executing your tests with that.
