# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool to generate Pimlico module docs. Based on Sphinx's apidoc tool.

"""
import argparse

import sys

import os
import warnings
from importlib import import_module
from pkgutil import iter_modules
from sphinx import __version__
from sphinx.apidoc import format_heading

from pimlico import install_core_dependencies
from pimlico.core.modules.options import format_option_type
from pimlico.datatypes import PimlicoDatatype, MultipleInputs, DynamicOutputDatatype, DynamicInputDatatypeRequirement
from pimlico.utils.docs import trim_docstring
from pimlico.utils.docs.rest import make_table


def generate_docs_for_pymod(module, output_dir):
    """
    Generate RST docs for Pimlico modules on a given Python path and output to a directory.

    """
    module_name = module.__name__
    # Look at all this module's submodules
    submodules = dict((modname, (importer, is_package)) for (importer, modname, is_package) in
                      iter_modules(module.__path__, prefix="%s." % module_name))

    # If not a Pimlico module, recurse into subpackages to find modules
    # Even if it is a Pimlico module, there could be other modules in the subpackages
    all_generated = []
    all_pimlico_modules = []
    all_children = []
    for modname, (importer, is_package) in sorted(submodules.items()):
        if is_package:
            # Import the module (package) so we can recurse on it
            submod = importer.find_module(modname).load_module(modname)
            is_pim_submod, sub_pim_mods = generate_docs_for_pymod(submod, output_dir)
            all_generated.append(submod.__name__)
            all_pimlico_modules.extend(sub_pim_mods)
            if is_pim_submod:
                all_children.append(submod.__name__)

    is_pimlico_module = False

    if "%s.info" % module_name in submodules and not submodules["%s.info" % module_name][1]:
        # This looks like a Pimlico module
        # Try building module docs for this one
        # If there were submodules, they should be included in the module doc in a TOC
        info = generate_docs_for_pimlico_mod(module_name, output_dir, all_generated)
        if info is not None:
            is_pimlico_module = True
            all_pimlico_modules.append(module_name)
    elif all_generated:
        # This was just a package, not a Pimlico module, but it included Pimlico modules
        # Generate a contents page for the submodules
        # If the submodule has a docstring, it goes onto the index page
        if module.__doc__ is not None and module.__doc__.strip("\n "):
            # By convention, the first line is used as a title
            module_title, __, module_doc = module.__doc__.lstrip("\n ").partition("\n")
        else:
            module_title = "Package %s" % module_name
            module_doc = ""
        # Generate an index for this submodule
        generate_contents_page(all_generated, output_dir, module_name, module_title, module_doc)

    # If no Pimlico modules were found anywhere in this package, don't generate anything
    return is_pimlico_module, all_pimlico_modules


def generate_docs_for_pimlico_mod(module_path, output_dir, submodules=[]):
    print "Building docs for %s" % module_path
    filename = os.path.join(output_dir, "%s.rst" % module_path)
    # First import the python module
    pymod = import_module(module_path)
    # Check whether we've been instructed to skip this module
    if hasattr(pymod, "SKIP_MODULE_DOCS") and pymod.SKIP_MODULE_DOCS:
        return

    # Import the info pymodule so we can get the ModuleInfo class
    info = import_module("%s.info" % module_path)  # We know this exists
    try:
        ModuleInfo = info.ModuleInfo
    except AttributeError:
        # If there's no ModuleInfo, it's not a valid Pimlico module
        # Warn, since it looks like it's supposed to be one
        warnings.warn("Module %s has no ModuleInfo in its info.py" % module_path)
        return

    # Collect key information from the module info
    key_info = [
        ["Path", module_path],
        ["Executable", "yes" if ModuleInfo.module_executable else "no"],
    ] + ModuleInfo.get_key_info_table()
    # Try using the module's readable name as the document title
    module_title = ModuleInfo.module_readable_name
    if module_title is None or module_title == "":
        # No readable name given: make one out of the internal name
        module_title = ModuleInfo.module_type_name
        module_title = module_title[0].capitalize() + module_title[1:]
        module_title = module_title.replace("_", " ")
    input_table = [
        [input_name, input_datatype_list(input_types, context=module_path)]
        for input_name, input_types in ModuleInfo.module_inputs
    ]
    output_table = [
        [output_name, output_datatype_text(output_types, context=module_path)]
        for output_name, output_types in ModuleInfo.module_outputs
    ]
    optional_output_table = [
        [output_name, output_datatype_text(output_types, context=module_path)]
        for output_name, output_types in ModuleInfo.module_optional_outputs
    ]
    info_doc = info.__doc__
    module_info_doc = ModuleInfo.__doc__

    additional_paras = []
    if ModuleInfo.is_input():
        additional_paras.append("This is an input module. It takes no pipeline inputs and is used to read in data")
    if ModuleInfo.is_filter():
        additional_paras.append(
            "This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can "
            "be run. It produces its output for the next module on the fly when the next module needs it."
        )

    # Put together the options table
    options_table = [
        [
            option_name,
            ("(required) " if d.get("required", False) else "") + d.get("help", ""),
            format_option_type(d.get("type", str)),
        ]
        for (option_name, d) in ModuleInfo.module_options.items()
    ]

    with open(filename, "w") as output_file:
        # Make a page heading
        output_file.write(format_heading(0, module_title))
        # Add a directive to mark this as the documentation for the py module that defines the Pimlico module
        output_file.write(".. py:module:: %s\n\n" % module_path)
        # Output a summary table of key information
        output_file.write("%s\n" % make_table(key_info))
        # Insert text from docstrings
        if info_doc is not None:
            output_file.write(trim_docstring(info_doc) + "\n\n")
        if module_info_doc is not None:
            output_file.write(trim_docstring(module_info_doc) + "\n\n")
        output_file.write("\n")
        output_file.write("".join("%s\n\n" % para for para in additional_paras))

        # Output a table of inputs
        output_file.write(format_heading(1, "Inputs"))
        if input_table:
            output_file.write("%s\n" % make_table(input_table, header=["Name", "Type(s)"]))
        else:
            output_file.write("No inputs\n\n")

        # Table of outputs
        output_file.write(format_heading(1, "Outputs"))
        if output_table:
            output_file.write("%s\n" % make_table(output_table, header=["Name", "Type(s)"]))
        elif optional_output_table:
            output_file.write("No non-optional outputs\n")
        else:
            output_file.write("No outputs\n")
        if optional_output_table:
            output_file.write("\n" + format_heading(2, "Optional"))
            output_file.write("%s\n" % make_table(optional_output_table, header=["Name", "Type(s)"]))

        # Table of options
        if options_table:
            output_file.write(format_heading(1, "Options"))
            output_file.write("%s\n" % make_table(options_table, header=["Name", "Description", "Type"]))

        if submodules:
            # Generate a TOC for the nested modules
            output_file.write(format_heading(1, "Submodules"))
            output_file.write(".. toctree::\n   :titlesonly:\n\n   ")
            output_file.write("\n   ".join(submodules))
            output_file.write("\n")
    return ModuleInfo


def input_datatype_list(types, context=None):
    if type(types) is tuple:
        # This is a list of types
        return " or ".join(input_datatype_text(t, context=context) for t in types)
    else:
        # Just a single type
        return input_datatype_text(types, context=context)


def input_datatype_text(datatype, context=None):
    if isinstance(datatype, PimlicoDatatype):
        # Standard behaviour for normal datatypes
        return ":class:`%s <%s>`" % (datatype.full_datatype_name(), datatype.datatype_full_class_name())
    elif isinstance(datatype, MultipleInputs):
        # Multiple inputs, but the datatype is known: call this function to format the common type
        return ":class:`list <pimlico.datatypes.base.MultipleInputs>` of %s" % \
               input_datatype_text(datatype.datatype_requirements)
    elif isinstance(datatype, DynamicInputDatatypeRequirement):
        if datatype.datatype_doc_info is not None:
            # Dynamic input type that gives us a name to use
            return datatype.datatype_doc_info
        else:
            # Dynamic datatype requirement with no custom string
            return ":class:`%s <%s.%s>`" % (type(datatype).__name__, type(datatype).__module__, type(datatype).__name__)
    else:
        warnings.warn("Invalid input type specification {} (not datatype, multiple input, or dynamic "
                        "requirement): {}".format("in {}".format(context) if context else "", type(datatype)))
        return "**invalid input type specification**"


def output_datatype_text(datatype, context=None):
    if isinstance(datatype, DynamicOutputDatatype):
        # Use the datatype name given by the dynamic datatype and link to the class
        datatype_class = datatype.get_base_datatype_class()
        if datatype_class is not None:
            datatype_class_name = datatype_class.datatype_full_class_name()
        else:
            # Just link to the dynamic datatype class
            datatype_class_name = "%s.%s" % (type(datatype).__module__, type(datatype).__name__)
        datatype_name = datatype.datatype_name or type(datatype).__name__
        return ":class:`%s <%s>`" % (datatype_name, datatype_class_name)
    elif isinstance(datatype, PimlicoDatatype):
        class_name = datatype.datatype_full_class_name()
        # Allow non-class datatypes to be specified in the string
        if class_name.startswith(":"):
            return class_name
        else:
            return ":class:`~{} <{}>`".format(
                datatype.datatype_full_class_name(),
                datatype.full_datatype_name()
            )
    else:
        warnings.warn("Invalid output type {} (not datatype or dynamic output type): {}".format(
            "in {}".format(context) if context else "", type(datatype))
        )
        return "**invalid output type specification**"


def generate_contents_page(modules, output_dir, index_name, title, content):
    with open(os.path.join(output_dir, "%s.rst" % index_name), "w") as index_file:
        index_file.write("""\
{title}
.. py:module:: {index_name}

{content}

.. toctree::
   :maxdepth: 2
   :titlesonly:

   {list}
""".format(
            title=format_heading(0, title),
            content=content,
            list="\n   ".join(modules),
            index_name=index_name,
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate module documentation RST files from core Pimlico modules, "
                                                 "or your own Pimlico modules")
    parser.add_argument("output_dir", help="Where to put the .rst files")
    parser.add_argument("--path", default="pimlico.modules",
                        help="Base Python module path to generate docs for. Defaults to generating docs for core "
                             "modules from the Pimlico distribution. Use this to generate module docs for your own "
                             "modules")
    opts = parser.parse_args()

    output_dir = os.path.abspath(opts.output_dir)

    # Install basic Pimlico requirements
    install_core_dependencies()

    print "Sphinx %s" % __version__
    print "Pimlico module doc generator"
    try:
        base_mod = import_module(opts.path)
    except ImportError, e:
        print "Could not import base module %s: %s" % (opts.path, e)
        print "Did you add your own modules to the pythonpath? (Current paths: %s)" % \
              u", ".join(sys.path).encode("ascii", "ignore")
        print "Cannot generate docs"
        sys.exit(1)
    print "Generating docs for %s (including all submodules)" % opts.path
    print "Outputting module docs to %s" % output_dir

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    generate_docs_for_pymod(base_mod, output_dir)
