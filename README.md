# gridt-server
This repository contains all the files necessary for creating a gridt network.

## Documentation
Our documentation is hosted on [readthedocs.io](https://gridt-server.readthedocs.io/).

## Setup
To run the repository simply run `docker-compose up` and in *theory* it should all run smoothly.

This part of the document is still very much a work in progress, but having some pointers might be useful. There are quite some security features built in, which rely on some well chosen passwords. Included in the toplevel of this branch you will find a file called 'generate_secret_key.py'. The output of this file is rather secure and can be used as a password for multiple places. In the docker-compose file the 'MYSQL_ROOT_PASSWORD' will have to be set. The same password will have to be set in the 'data/web/gridt.conf' file. The secret key of the flask application will also have to be set by creating a new file in 'data/web/' called 'flask_secret_key.txt'. The easiest way of creating this is by running `./generate_secret_key.py > data/web/flask_secret_key.txt`. Careful that there are no extra lines in the file, there can be only one!


## Contribution
Great that you are considering contributing to our project. Feel free to donate [money](gridt.opencollective.com) or [code](CONTRIBUTION_GUIDELINES).

## License
The Gridt Network - the network for connecting social movements. Copyright (C) 2020, Stichting Gridt

E-mail: info@gridt.org

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
