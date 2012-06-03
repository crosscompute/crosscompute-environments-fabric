VIRTUAL_ENV=$HOME/.virtualenv
sudo service sshd start
(sudo yum -y install fabric) && fab -H localhost install:$VIRTUAL_ENV
