
# Local dev stack

To run locally on Windows, Linux, macOS, etc. without AWS services:

    Setup access to code repo
    Install latest Python 3.9
    (pip and python commands below assumes 3.9 is default, adjust if needed)

    Create Python virtual environment:

        > python -m venv .venv
        > .venv\Scripts\activate

    Setup new virtual environment:

        > python -m pip install --upgrade pip
        > pip install -r mpframework\deploy\pip_shared.txt
        > pip install -r mpframework\deploy\pip_dev.txt

    Use the following to see commands:

        > fab -l

    Run a local server:

        > fab clean     (create new local DB, may need to run twice first time)
        > fab static    (Move static JS/CSS files)
        > fab run       (Start server on 0.0.0.0:80)

    To build and run a local dev container:

        > docker build . --progress plain -t mpf
        > docker run -itd --name mpf -p 8080:80 mpf

## .secrets folder

Some dev, test, and deployment tools use Fabric SSH to connect to remote servers. To use these tools a .secrets folder must be created as a sibling to the MPF monorepos that contains:

    public SSH keys for server keypairs in subfolders by root platform
