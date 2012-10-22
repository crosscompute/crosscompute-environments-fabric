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
    # Enter virtual environment
    v

Use Fedora AMI.

    # Go to https://fedoraproject.org/wiki/Cloud_images
    # Use us-east-1 x86_64 EBS-backed ami-2ea50247 
    # Go to https://console.aws.amazon.com/ec2
    # Search for ami-2ea50247 in Images > AMIs
    # Launch High-CPU Medium instance with open ports 22 and 443
    # Load SSH certificate
    AMI_CERTIFICATE=~/.ssh/YOUR-CERTIFICATE.pem
    chmod 400 $AMI_CERTIFICATE
    ssh-add $AMI_CERTIFICATE

Associate Elastic IP.

    # Go to https://console.aws.amazon.com/ec2
    # Go to Network & Security > Elastic IPs
    # Allocate New Address
    # Associate Address with desired instance

Prepare Private CrossCompute AMI.

    cd $CC_SCRIPTS
    AMI_URI=ec2-user@YOUR-ELASTIC-IP
    fab install install_node -H $AMI_URI
    # Backup AMI

    fab configure_ipython_notebook -H $AMI_URI
    # Reboot instance
    # Go to https://YOUR-ELASTIC-IP
    # Go to https://console.aws.amazon.com/ec2
    # Stop image
    # Create Private CrossCompute AMI

Prepare Public CrossCompute AMI.

    # Clear sensitive information
        fab prepare_image -H $AMI_URI
    # Go to https://console.aws.amazon.com/ec2
    # Stop instance
    # Create image


Deploy AMI
----------
Use CrossCompute AMI.

    # Go to https://console.aws.amazon.com/ec2
    # Search for ami-64f34c0d in Images > AMIs
    # Launch High-CPU Medium instance with open ports 22 and 443
    # Load SSH certificate
    AMI_CERTIFICATE=~/.ssh/YOUR-CERTIFICATE.pem
    chmod 400 $AMI_CERTIFICATE
    ssh-add $AMI_CERTIFICATE

Associate Elastic IP.

    # Go to https://console.aws.amazon.com/ec2
    # Go to Network & Security > Elastic IPs
    # Allocate New Address
    # Associate Address with desired instance

Configure IPython server passwords and SSL certificates.

    cd $CC_SCRIPTS
    AMI_URI=ec2-user@YOUR-ELASTIC-IP
    fab configure_ipython_notebook -H $AMI_URI

Harden server security for workshops.

    fab harden_server -H $AMI_URI
