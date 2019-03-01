# gridt-server

## Config files
When you have your local install of the gridt-server, you will have to add a secret key to at least one config file, to which you will have to refer using the environment variable `FLASK_CONFIGURATION`. The suggested folder for this is `conf/`.

## Run
To run the application make sure you are in the correct environment by running `$pipenv shell` in (a subfolder of) gridt-server. Alternatively you can use `pipenv run <your command>`. Then you can start the application by giving the `$flask run` command.
