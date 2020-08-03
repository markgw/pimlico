# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool to generate Pimlico docs for example config files.

Each example config file is (for now) just shown in full in the docs.
"""
from __future__ import print_function

import argparse
import os
import warnings
from itertools import takewhile, dropwhile

from pimlico import install_core_dependencies, EXAMPLES_DIR, REPO_SOURCE_HTML_ROOT, \
    PIMLICO_ROOT
from pimlico.core.config import PipelineConfig
from pimlico.utils.docs.modulegen import indent
from .rest import format_heading

DOC_TEMPLATE = """\
.. _{ref_name}:

{title}

This is an example Pimlico pipeline.

{code_intro}

Pipeline config
===============

.. code-block:: ini
   
{config_text}

{module_list}

"""

INDEX_TEMPLATE = """\
.. _example-pipelines:

Example pipelines
~~~~~~~~~~~~~~~~~

Pimlico comes with a number of example pipelines to demonstrate how to 
use it. 

A more extensive set of examples is also provided in the form of 
:ref:`test pipelines <test-pipelines>`, which give a small example of the 
usage of individual core modules and are used as unit tests for the modules.

Available pipelines
===================

.. toctree::
   :maxdepth: 2
   :titlesonly:

   {generated}


Running
=======

To run example pipelines, you can use the script ``run_example.sh`` in Pimlico's 
``example`` directory, e.g.:

.. code-block:: sh
   
   ./example_pipeline.sh simple/tokenize.conf status

This will load a single example pipeline from the given config file and show the 
execution status of the modules.

"""


def build_example_config_doc(base_path, rel_path):
    conf_file = os.path.join(base_path, rel_path)
    root_rel = os.path.relpath(conf_file, PIMLICO_ROOT)

    # Load the raw data
    with open(conf_file, "r") as f:
        conf_data = f.read()
    if conf_data.startswith("# TODO"):
        # This example pipeline is not ready to be included: skip it
        warnings.warn("Skipping pipeline {}, since it starts with a TODO".format(conf_file))
        return

    # Use the special local config file for examples
    examples_lc_path = os.path.join(EXAMPLES_DIR, "examples_local_config")

    # Try loading the test pipeline
    try:
        pipeline = PipelineConfig.load(conf_file, local_config=examples_lc_path)
    except Exception as e:
        warnings.warn("Could not load example pipeline {}: {}. Not building doc".format(conf_file, e))
        return

    # Look for initial comments and extract them to the page text
    lines = conf_data.splitlines()
    try:
        first_non_comment = next(dropwhile(lambda nl: nl[1].startswith("#"), enumerate(lines)))[0]
    except StopIteration:
        first_non_comment = 0
    initial_comments = "\n".join(line[2:] for line in lines[:first_non_comment])
    # Drop any blank lines from the start
    conf_data = "\n".join(dropwhile(lambda l: not l.strip(), lines[first_non_comment:]))

    # Generate a link to the source code
    source_url = "{}{}".format(REPO_SOURCE_HTML_ROOT,
                               "/".join(root_rel.split(os.path.sep)))

    code_intro = "The complete config file for this example pipeline is below. `Source file <{}>`_\n\n{}"\
        .format(source_url, initial_comments)

    # Check what module types are used
    module_types = [m.module_package_name() for m in pipeline]
    # Some modules will have no package name identifying them, as they're dataset loaders
    module_types = [m for m in module_types if m and m.startswith("pimlico.modules")]

    if len(module_types):
        module_list = """\
{}
The following Pimlico module types are used in this pipeline:

{}
    """.format(
            format_heading(1, "Modules"),
            "\n".join(" * :mod:`{}`".format(mod) for mod in module_types)
        )
    else:
        module_list = ""

    # Use the pipeline name as the reference
    ref_name = "example-pipeline-{}".format(pipeline.name.replace("_", "-"))

    return DOC_TEMPLATE.format(
        title=format_heading(0, pipeline.name),
        ref_name=ref_name,
        config_text=indent(3, conf_data),
        code_intro=code_intro,
        module_list=module_list
    ), ref_name, module_types


def build_index(generated, output_dir):
    with open(os.path.join(output_dir, "index.rst"), "w") as f:
        f.write(INDEX_TEMPLATE.format(
            generated="\n   ".join(generated)
        ))
    print("Wrote index to {}".format(os.path.join(output_dir, "index.rst")))


def build_example_config_docs(example_config_dir, output_dir):
    generated = []
    module_refs = []

    for base_dir, dirs, filenames in os.walk(example_config_dir):
        for filename in filenames:
            if filename.endswith(".conf"):
                # Get the path relative to the test base
                rel_path = os.path.relpath(base_dir, example_config_dir)
                if rel_path == ".":
                    rel_path = ""
                ex_rel_path = os.path.join(rel_path, filename)
                print("Building {}".format(ex_rel_path))
                # Build the doc's text
                doc = build_example_config_doc(example_config_dir, ex_rel_path)
                if doc is not None:
                    doc_text, ref_name, modules = doc
                    # Work out what to call the file
                    out_filename = ex_rel_path.replace(".conf", ".rst").replace(os.path.sep, ".")
                    with open(os.path.join(output_dir, out_filename), "w") as f:
                        f.write(doc_text)
                    print("  Written to {}".format(out_filename))
                    generated.append(out_filename)
                    module_refs.append((ref_name, modules))

    if len(set(generated)) < len(generated):
        warnings.warn("Multiple test config files were found with the same name")

    build_index(generated, output_dir)

    # Output a list of what modules are used by what tests
    # This will be read in by the module doc builder to include a list in each module's docs
    module_list_fn = os.path.join(output_dir, "module_list.tsv")
    with open(module_list_fn, "w") as f:
        f.write("\n".join("{}\t{}".format(ref_name, ", ".join(modules)) for (ref_name, modules) in module_refs))
    print("Module reference list output to {}".format(module_list_fn))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate documentation RST files from Pimlico example config files")
    parser.add_argument("output_dir", help="Where to put the .rst files")
    opts = parser.parse_args()

    output_dir = os.path.abspath(opts.output_dir)

    # Install basic Pimlico requirements
    install_core_dependencies()

    print("Pimlico example config doc generator")

    if not os.path.exists(EXAMPLES_DIR):
        print("Example config dir could not be found: {}".format(EXAMPLES_DIR))
    else:
        print("Building example config docs from pipelines found in {}".format(EXAMPLES_DIR))

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    build_example_config_docs(EXAMPLES_DIR, output_dir)
