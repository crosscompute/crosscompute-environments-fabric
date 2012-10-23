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

Associate Elastic IP.

    # Go to https://console.aws.amazon.com/ec2
    # Go to Network & Security > Elastic IPs
    # Allocate New Address
    # Associate Address with desired instance

Prepare Private CrossCompute AMI.

    AMI_URI=ec2-user@YOUR-ELASTIC-IP
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
    # Go to https://YOUR-ELASTIC-IP
    # Go to https://console.aws.amazon.com/ec2
    # Create Private CrossCompute AMI

Prepare Public CrossCompute AMI.

    # Clear sensitive information
        fab prepare_image -H $AMI_URI
    # Go to https://console.aws.amazon.com/ec2
    # Create Public CrossCompute AMI


Deploy AMI
----------
Use CrossCompute AMI.

    # Go to https://console.aws.amazon.com/ec2
    # Click on Images > AMIs
    # If your region is us-east-1, search for ami-d65fe6bf
    # If your region is us-west-2, search for ami-bc850c8c
    # If your region is sa-east-1, search for ami-4221f85f
    # Launch High-CPU Medium instance with open ports 22 and 443

Associate Elastic IP.

    # Go to https://console.aws.amazon.com/ec2
    # Go to Network & Security > Elastic IPs
    # Allocate New Address
    # Associate Address with desired instance

Configure IPython server passwords and SSL certificates.

    AMI_URI=ec2-user@YOUR-ELASTIC-IP
    AMI_CERTIFICATE=~/.ssh/YOUR-CERTIFICATE.pem
    CC_SCRIPTS=~/Documents/crosscompute-scripts

    # Load SSH certificate
    chmod 400 $AMI_CERTIFICATE
    ssh-add $AMI_CERTIFICATE
    # Enter virtual environment
    v
    # Configure server
    cd $CC_SCRIPTS
    fab configure_ipython_notebook -H $AMI_URI

Harden server security for workshops (optional).

    fab prepare_workshop -H $AMI_URI
