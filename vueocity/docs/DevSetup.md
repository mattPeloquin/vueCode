
Vueocity Dev Setup
==================

MPF Dev environments support local dev, testing, and command line AWS DevOps activities.

## Windows dev notes

Windows is different from Linux...

 - Set UNICODE settings for LOCALE to prevent errors when using a terminal window:

    1) Language Settings | Administrative Language Settings | Change System Locale
    2) Select "Beta: User Unicode UTF-8 for worldwide language support"
    3) Accept restart

 - Python multithreading doesn't respond well to a Ctrl-C break in command windows. Use a Ctrl-Pause to break instead.

 - UNPROTECTED PRIVATE KEY FILE error with SSH:
    change .secrets folder to full control of windows user account.

 - REMOTE HOST IDENTIFICATION HAS CHANGED! error with ssh and new AMI:
    remove C:\users\_username_\.ssh\known_hosts

# Setting up a dev machine

The steps below will create a LOCAL Vueocity dev stack that can run unit tests and interactive browser testing.

    0) Local machine prerequisites
        a) Latest version Windows 10, Mac, or Linux
        b) Install Chrome as reference browser (if not already)
        c) Install C/C++ compiler needed for some Python pip installs:
            Windows (Visual C++ 14.x):
                https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16
                Run and select "Desktop development with C++"

    1) Install TortoiseHg with Mercurial (hg)

        TBD - switch to git and signed keys with github

        Get invite from code repo, verify access through web.
        Download and install the following, accepting defaults:

            https://tortoisehg.bitbucket.io/

        Turn on keyring capability:
            Open "mecurial.ini" under "c:\Users\*your windows user*
            Add the following lines:

                [extensions]
                mercurial_keyring=

        Then clone MPF repo:
            Right-click c: drive under PC in file explorer
            Select "TortoiseHg | Clone..."
            Update the dialog with text below, replacing [user] with
            your repo username:

                Source: https://[user]@vue.xp-dev.com/hg/VueMono1
                Dest:   c:\vueCode

                Enter pwd when prompted

            Now try a pull - you will be prompted about removing credentials from url, hit OK and then save default.
            Username and pwd is now stored.

            To open in future right click on c:\vueCode and run "Hg Workbench".

    2) Install latest Python 3.9 (64-bit)

            https://www.python.org/downloads/

        Run the install. Use default settings EXCEPT:

            - ENABLE "Add python 3.9 to PATH"
            - Optionally place Python in your own tools folder

        After install, open a comand/shell window (windows_key-R, then type cmd)
        and run Python to test install:

            > python -V

        See troubleshooting below if Python doesn't run

    3) Create virtual environment
    Python virtual environments (venv) isolate Python tools/libs in a project folder.

        a) WINDOWS - Find the file below and pin it to taskbar or desktop:
            c:\vueCode\vueocity\deploy\win\vueCode.lnk

        b) From command-line window install venv:
            WINDOWS - use the link from step 3a to open window

            > python -m venv .venv

        c) Activate the virtual environment
            WINDOWS - Close the command-line window and reopen
            MAC, LINUX - Run: .venv/Scripts/activate

            You should see a prompt like below:

            (.venv) c:\vueCode>

    4) Setup virtual environment
    Add dependencies needed by MPF, defined in pip config files.

        Run the following at venv command prompt:

            > pip install -r mpframework\deploy\pip_shared.txt
            > pip install -r mpextend\deploy\pip_shared.txt
            > pip install -r mpframework\deploy\pip_dev.txt
            > pip install -r vueocity\deploy\pip_dev.txt

    Close and reopen shell and MPF dev environment is ready to go!

    Use the following to see commands:

        > fab -l

    Run a local server:

        > fab clean     (create new local DB)
        > fab static    (Move static JS/CSS files)
        > fab run       (Start server on 0.0.0.0:80)

## AWS dev access

To work with AWS environments, additional setup is needed:

    1) Setup AWS accounts(s) and get invite and role info

    2) SSH directly to EC2 servers

        Add SSH port and IP to security group for the servers.
        Add private keypair files for any SSH connections to .secrets

        Windows: There is a batch file and shortcut under deploy\windows for running ssh with default production key.

    3) Install AWS Command Line Interface

        Linux: Should already be part of distro in Amazon Linux
            pip install awscli

        Windows: Download installer

            https://awscli.amazonaws.com/AWSCLIV2.msi

    4) Configure local machine to run CLI with IAM role profiles. Follow instructions in:

        vueocity/deploy/aws/IAM/ReadMe.md

    5) To setup infrastructure in AWS accounts:

     - Download Terraform and Terragrunt exes and add their location to PATH
        (can also use package manager like chocolatey or howebrew)

    6) To use 'fab a' a local machine must have an aws.yaml file in the .secrets folder.
    TBD NOW SECURE - dependency on local aws.yaml file will be removed.

# Browser setup

    Chrome is reference browser, but FireFox, Edge, and Safari should be available, including mobile versions.
    All desktop browsers include F12 key debugger support. Remote debugging is used for mobile, but is not normally needed.

    For Selenium testing, browser WebDriver exe files need to be copied to the .tools folder:

        [Chrome](https://sites.google.com/a/chromium.org/chromedriver/downloads)
        [Edge](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
        [Firefox](https://github.com/mozilla/geckodriver/releases/)

    Other useful utilities:
        FireBug debugger
        FirePath, XPath Checker for xpath resolution
        SQLite Manager for viewing with dev DBs

# Code editors/IDE

Visual Studio Code is preferred editor.

    A standard workspace config in revision control
    The following extensions should be installed:
        Python
        Hg
        vscode-icons
        Code Spell Checker

## Debugging and local testing

Bench testing and automated tests are executed from fab commands.
Server and Python test debugging can occur in VS Code if configured for Python.
Client debugging always occurs in browser F12.

# Other Linux Dev

Ubuntu or some other Linux environment for development (either locally or hosted at AWS)
hasn't been set up, but should be easy.

# macOS Dev

Although it would be easier than windows to install nginx, uwsgi, mysql etc. and actually
run in a server configuration, there isn't much point to wasting time dealing
with any environment differences from the Amazon servers. Use same approach as
with Windows -- run django web server with sqllite locally.

Thus working pattern in mac is essentially the same as in Windows; work
on files locally, push changes onto servers.

No active mac sandbox is going right now, but steps from prototyping are below:

    To start with, install XCode (for gcc, even if you won't use IDE)
    Recommend using MacHg for mercurial
    Create a mpFramework folder in your users dir or whereever, and clone repository
    Install pip as described in AmiSetup.
    Install MacPorts (so you can use 'port' in place of 'yum')
    Next, create virtual environment, activate it, and install dependencies as described in install.sh, but skip nginx, uwsgi, and mysql items

# Linux Server Dev

1) Server - via Amazon server with the Amazon LinuxAMIs,
so setup a server and log in, vim away.
This is the only dev environment where nginx and uwsgi are installed.

2) Use Ubuntu, and follow server setup steps
