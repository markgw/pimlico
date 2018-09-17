# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool to generate Pimlico docs for test config files.

Build this before building `modules`, so that the list of modules referenced in
test pipelines is ready.

"""
import argparse
import os
import warnings
from sphinx import __version__
from sphinx.apidoc import format_heading

from pimlico import install_core_dependencies, TEST_DATA_DIR, TEST_STORAGE_DIR
from pimlico.test.pipeline import TestPipeline
from pimlico.utils.docs.modulegen import indent

DOC_TEMPLATE = """\
.. _{ref_name}:

{title}

This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

{code_intro}

.. code-block:: ini
   
{config_text}


{module_list}

"""

INDEX_TEMPLATE = """\
.. _test-pipelines:

Module test pipelines
~~~~~~~~~~~~~~~~~~~~~

.. todo::
   
   Write introduction to test pipelines


.. toctree::
   :maxdepth: 2
   :titlesonly:

   {generated}

"""


def build_test_config_doc(conf_file):
    config_name = os.path.basename(conf_file)
    ref_name = "test-config-{}".format(config_name)

    # Load the raw data
    with open(conf_file, "r") as f:
        conf_data = f.read()

    # Try loading the test pipeline
    try:
        pipeline = TestPipeline.load_pipeline(conf_file, TEST_STORAGE_DIR)
    except Exception, e:
        warnings.warn("Could not load test pipeline {}: {}. Not building doc".format(conf_file, e))
        return

    code_intro = "{}The complete config file for this test pipeline:\n".format(format_heading(1, "Config file"))

    # Check what module types are used
    module_types = [m.module_package_name() for m in pipeline]
    # Some modules will have no package name identifying them, as they're dataset loaders
    module_types = [m for m in module_types if m]

    if len(module_types):
        module_list = """\
{}
The following Pimlico module types are used in this pipeline:

{}
    """.format(
            format_heading(1, "Modules"),
            "\n".join(" * :mod:`~{}`".format(mod) for mod in module_types)
        )
    else:
        module_list = ""

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
    print "Wrote index to {}".format(os.path.join(output_dir, "index.rst"))


def build_test_config_docs(test_config_dir, output_dir):
    generated = []
    module_refs = []

    for base_dir, dirs, filenames in os.walk(test_config_dir):
        for filename in filenames:
            if filename.endswith(".conf"):
                # Get the path relative to the test base
                rel_path = os.path.relpath(base_dir, test_config_dir)
                print "Building {}/{}".format(rel_path, filename)
                # Build the doc's text
                doc = build_test_config_doc(os.path.join(base_dir, filename))
                if doc is not None:
                    doc_text, ref_name, modules = doc
                    # Work out what to call the file
                    out_filename = "{}.{}.rst".format(".".join(x for x in os.path.split(rel_path) if x), filename)
                    with open(os.path.join(output_dir, out_filename), "w") as f:
                        f.write(doc_text)
                    print "  Written to {}".format(out_filename)
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
    print "Module reference list output to {}".format(module_list_fn)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate documentation RST files from Pimlico test config files")
    parser.add_argument("output_dir", help="Where to put the .rst files")
    opts = parser.parse_args()

    output_dir = os.path.abspath(opts.output_dir)

    # Install basic Pimlico requirements
    install_core_dependencies()

    print "Sphinx %s" % __version__
    print "Pimlico test config doc generator"

    test_config_dir = os.path.join(TEST_DATA_DIR, "pipelines")
    if not os.path.exists(test_config_dir):
        print "Test config dir could not be found: {}".format(test_config_dir)
    else:
        print "Building test config docs from pipelines found in {}".format(test_config_dir)

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    build_test_config_docs(test_config_dir, output_dir)
