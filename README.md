crosscompute-scripts
====================
Here is a [fabric](http://docs.fabfile.org) script for preparing a scientific computing environment in [Fedora](http://fedoraproject.org).

    # Add yourself to sudoers
    su
        vim /etc/sudoers
            root          ALL=(ALL) ALL
            YOUR_USERNAME ALL=(ALL) ALL

    # Run script
    git clone https://github.com/invisibleroads/crosscompute-scripts.git
    cd crosscompute-scripts
    bash fabfile.sh | tee crosscompute-scripts.log
