"""
A command to start a Jupyter notebook for a given pipeline, providing access
to its modules and their outputs.

"""
import json
import os
import sys

from future.utils import PY3

from pimlico import PIMLICO_ROOT
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.core.dependencies.python import PythonPackageOnPip


class JupyterCmd(PimlicoCLISubcommand):
    command_name = "jupyter"
    command_help = "Create and start a new Jupyter notebook for the pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--notebook-dir", action="store",
                            help="Use a custom directory as the notebook directory. By default, a directory will be "
                                 "created according to: <pimlico_root>/../notebooks/<pipeline_name>/")

    def run_command(self, pipeline, opts):
        if not jupyter_dependency.available(pipeline.local_config):
            print("Jupyter not currently installed in local environment: installing")
            jupyter_dependency.install(pipeline.local_config)
        # Now Jupyter should be installed, so we can import the main function for running notebooks
        from notebook.notebookapp import main
        print("Jupyter installed and successfully imported")

        # Set up a directory that will be used as the notebook directory for this pipeline
        if opts.notebook_dir is not None:
            notebook_dir = opts.notebook_dir
            print("Using custom notebook directory: {}".format(notebook_dir))
        else:
            notebook_dir = os.path.abspath(os.path.join(PIMLICO_ROOT, "..", "notebooks", pipeline.name))
            print("Using notebook directory for pipeline {}: {}".format(pipeline.name, notebook_dir))
        # Create the directory tree if necessary
        if not os.path.exists(notebook_dir):
            print("Creating notebook dir {}".format(notebook_dir))
            os.makedirs(notebook_dir)
            # Create an example source file that loads the pipeline
            if len(pipeline.modules) == 0:
                # Can't give an example module name, as there aren't any modules
                example_module_name = "module_name"
                example_output = "output_name"
            else:
                example_module_name = pipeline.modules[-1]
                example_mod = pipeline[example_module_name]
                if len(example_mod.available_outputs) == 0:
                    # Can't give example output name, as the module doesn't have any outputs
                    example_output = "output_name"
                else:
                    example_output = example_mod.available_outputs[0]
            example_code = EXAMPLE_CODE.format(
                example_module_name=example_module_name,
                example_output_name=example_output
            )
            print("Adding example notebook")
            with open(os.path.join(notebook_dir, "example.ipynb"), "w") as f:
                f.write(make_notebook(example_code))

        # Make the currently loaded pipeline available from within Jupyter notebooks via an environment var
        os.environ["JUPYTER_PIPELINE"] = os.path.abspath(pipeline.filename)

        print("Running Jupyter...")
        print("------------------")
        print("From within a notebook, you can access the loaded '{}' pipeline by:")
        print("  from pimlico import get_jupyter_pipeline")
        print("  pipeline = get_jupyter_pipeline()")
        print()
        sys.argv = [sys.argv[0], "--notebook-dir", notebook_dir]
        sys.exit(main())


jupyter_dependency = PythonPackageOnPip("jupyter")


EXAMPLE_CODE = """\
# This is an example of how to load your pipeline from a notebook
from pimlico import get_jupyter_pipeline

pipeline = get_jupyter_pipeline()

# Now you can access the modules of the pipeline through this pipeline object
mod = pipeline["{example_module_name}"]

# And get data from its outputs (provided the module's been run)
print(mod.status)

output = mod.get_output("{example_output_name}")
"""


def make_notebook(code_text):
    data = {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2,
    }
    for line in code_text.split("\n\n"):
        data["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line],
        })
    return json.dumps(data, indent=4)
