#!/usr/bin/env bash

THIS=$(perl -MCwd -le 'print Cwd::abs_path(shift)' "${BASH_SOURCE[0]}")
DIR=$(dirname $THIS)

# Add Pimlico-specific Python library location
export PYTHONPATH=$PYTHONPATH:$DIR/../src/python

# By default, use Python 3
PYTHON_CMD=python3
VENV_NAME=default
VENV_DIR=

usage() {
    echo "Usage: $0 [ -2 ] [ -p PYTHON_CMD ]" 1>&2
}
exit_abnormal() {
    usage
    exit 1
}

while getopts "2p:n:hv:" options; do
    case "${options}" in
        2)
            # Use Python 2
            PYHTON_CMD=python2
            ;;
        p)
            # Use another Python interpreter, specified as a path to the command
            PYTHON_CMD=${OPTARG}
            ;;
        n)
            VENV_NAME=${OPTARG}
            ;;
        v)
            VENV_DIR=${OPTARG}
            ;;
        h)
            usage
            echo
            echo "  -2      Use Python 2. By default Python"
            echo "          3 is used."
            echo "  -p <PATH>   Use the given Python "
            echo "          interpreter."
            echo " -n <NAME>    Use the given name for the "
            echo "          virtual environment. If not given, "
            echo "          the name \"default\" is used."
            echo " -v <DIR> Specify the full path to the "
            echo "          virtual env that will be created."
            ;;
        :)
            # Expected argument omitted
            echo "Error: -${OPTARG} requires an argument."
            exit_abnormal
            ;;
        *)
            exit_abnormal
            ;;
    esac
done

if [ -z "$VENV_DIR" ]; then
    VENV_DIR="$DIR/../lib/virtualenv/$VENV_NAME"
fi

echo "Virtual env dir: $VENV_DIR"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment directory $VENV_DIR"
    echo "already exists: not creating a new venv."
    exit 1
fi

# Run the Python script to create the venv
$PYTHON_CMD $DIR/../lib/libutils/create_virtualenv.py $VENV_DIR


if [ "$?" != "0" ]; then
    # Failed to set up virtualenv: don't carry on running
    exit 1
fi

python=$VENV_DIR/bin/python

if [ ! -f "$python" ]; then
    echo "Virtualenv setup seemed to work, but Python interpreter $python is still not available"
    exit 1
fi
echo "Successfully set up virtualenv for running Pimlico. Running basic Pimlico setup"

echo "Installing essential initial dependencies"
$VENV_DIR/bin/pip install -r $DIR/../lib/libutils/requirements.txt

# If we've just installed the virtualenv then there'll be basic setup to be done
# Run Pimlico in its special first-run setup mode that doesn't require loading a pipeline
echo "Running basic Pimlico setup"
$python -m pimlico.cli.main setup
