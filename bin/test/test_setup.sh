#!/usr/bin/env bash
# A test that runs the setup of a new project, exactly as a user would do
DIR="$(cd "$( dirname $( readlink -f "${BASH_SOURCE[0]}" ))" && pwd )"
PYTHON_CMD=python3
PIM_BRANCH=python3

# Install the project (with pipeline and pimlico subdir) to a temporary dir
STORAGE_DIR="$(cd $DIR/../../test/storage && pwd)"
PROJ_DIR=$STORAGE_DIR/myproj
echo "Creating test Pimlico projects in $PROJ_DIR"
rm -rf $PROJ_DIR
mkdir $PROJ_DIR

echo "Creating a project test_proj1 using newproject.py"
# Put newproject.py from the current codebase into the project dir
# Also put bootstrap.py there, so that newproject.py uses the current version
# instead of downloading it from the repo, as it usually would
cd $PROJ_DIR
cp $DIR/../../admin/newproject.py .
cp $DIR/../../admin/bootstrap.py .

# Run newproject.py to initialise Pimlico
$PYTHON_CMD newproject.py --git --branch $PIM_BRANCH test_proj1

# Remove the temporary project dir
rm -rf $PROJ_DIR
