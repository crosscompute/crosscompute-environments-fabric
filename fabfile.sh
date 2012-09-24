sudo service sshd start
VIRTUALENV_HOME=~/.virtualenvs
VIRTUALENV_NAME=crosscompute
(sudo yum -y install fabric) && fab -H localhost --set virtualenvHome=$VIRTUALENV_HOME,virtualenvName=$VIRTUALENV_NAME
