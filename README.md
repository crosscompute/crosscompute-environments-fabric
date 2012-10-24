CrossCompute Scripts
====================
Here are [fabric](http://docs.fabfile.org) scripts for preparing a scientific computing environment in [Fedora](http://fedoraproject.org).

    # Add yourself to sudoers
    su
        vim /etc/sudoers
            root          ALL=(ALL) ALL
            YOUR-USERNAME ALL=(ALL) ALL

    # Run script
    git clone https://github.com/invisibleroads/crosscompute-scripts.git
    cd crosscompute-scripts
    bash fabfile.sh | tee crosscompute-scripts.log


Prepare AMI
-----------
AMI stands for Amazon Machine Image.

    # Go to https://console.aws.amazon.com/ec2

Prepare host.

    CC_SCRIPTS=~/Documents/crosscompute-scripts
    git clone https://github.com/invisibleroads/crosscompute-scripts.git $CC_SCRIPTS
    cd $CC_SCRIPTS
    bash fabfile.sh install_base install_ipython

Use Fedora AMI.

    # Go to https://fedoraproject.org/wiki/Cloud_images
    # Use us-east-1 x86_64 EBS-backed ami-2ea50247 
    # Go to https://console.aws.amazon.com/ec2
    # Search for ami-2ea50247 in Images > AMIs
    # Launch High-CPU Medium instance with open ports 22 and 443

Prepare Server CrossCompute AMI.

    AMI_URI=ec2-user@ec2-YOUR-INSTANCE.compute-XXX.amazonaws.com
    AMI_CERTIFICATE=~/.ssh/YOUR-CERTIFICATE.pem
    CC_SCRIPTS=~/Documents/crosscompute-scripts

    # Load SSH certificate
    chmod 400 $AMI_CERTIFICATE
    ssh-add $AMI_CERTIFICATE
    # Enter virtual environment
    v
    # Prepare server
    cd $CC_SCRIPTS
    fab install install_node -H $AMI_URI
    # Create Console CrossCompute AMI

    # Configure server
    fab configure_ipython_notebook -H $AMI_URI
    # Reboot instance
    # Go to https://ec2-YOUR-INSTANCE.compute-XXX.amazonaws.com
    # Go to https://console.aws.amazon.com/ec2
    # Create Server CrossCompute AMI

Prepare Public CrossCompute AMI.

    # Clear sensitive information
        fab prepare_image -H $AMI_URI
    # Go to https://console.aws.amazon.com/ec2
    # Create Public CrossCompute AMI


Use AMI
-------
Use CrossCompute AMI.

    # Go to https://aws.amazon.com/search?searchQuery=crosscompute
    # Launch a High-CPU Medium instance.
    # Proceed without a Key Pair.
    # Create a new Security Group > Add Rule: HTTPS.
    # Wait a few minutes.
    # Use a browser that supports websockets (Chrome, Firefox, Safari) and go to https://ec2-YOUR-INSTANCE.compute-XXX.amazonaws.com

The default IPython Notebook server password is <b>hahaha.com</b>.


Customize AMI
-------------
Reset IPython Notebook server passwords and SSL certificates.

    fab configure_ipython_notebook -H $AMI_URI


Teach a workshop with the AMI
-----------------------------
Make notebooks read-only for workshops.

    fab prepare_workshop -H $AMI_URI

Associate Elastic IP.

    # Go to https://console.aws.amazon.com/ec2
    # Go to Network & Security > Elastic IPs
    # Allocate New Address
    # Associate Address with desired instance
