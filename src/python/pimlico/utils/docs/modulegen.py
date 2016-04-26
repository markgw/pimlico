"""
Tool to generate Pimlico module docs. Based on Sphinx's apidoc tool.

"""
import argparse
import os
import warnings
from importlib import import_module
from pkgutil import walk_packages, iter_modules

from sphinx import __display_version__
from sphinx.apidoc import format_heading

import pimlico.modules
from pimlico.core.modules.options import format_option_type
from pimlico.datatypes.base import DynamicOutputDatatype, PimlicoDatatype
from pimlico.utils.docs import trim_docstring
from pimlico.utils.docs.rest import make_table


def generate_docs(output_dir):
    """
    Generate RST docs for all core Pimlico modules and output to a directory.

    """
    generated = generate_docs_for_pymod(pimlico.modules, output_dir)
    # Build a contents page for the modules
    generate_contents_page(generated, output_dir)


def generate_docs_for_pymod(module, output_dir):
    module_name = module.__name__
    # Look at all this module's submodules
    submodules = dict((modname, (importer, is_package)) for (importer, modname, is_package) in
                      iter_modules(module.__path__, prefix="%s." % module_name))

    if "%s.info" % module_name in submodules and not submodules["%s.info" % module_name][1]:
        # This looks like a Pimlico module
        # Don't recurse to submodules, but trying building module docs for this one
        return [generate_docs_for_pimlico_mod(module_name, output_dir)]
    else:
        # Not a Pimlico module: recurse into subpackages
        all_generated = []
        for modname, (importer, is_package) in sorted(submodules.items()):
            if is_package:
                # Import the module (package) so we can recurse on it
                submod = importer.find_module(modname).load_module(modname)
                generated = generate_docs_for_pymod(submod, output_dir)
                all_generated.extend(generated)
        return all_generated


def generate_docs_for_pimlico_mod(module_path, output_dir):
    print "Building docs for %s" % module_path
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
    ]
    input_table = [
        [input_name, input_datatype_list(input_types)] for input_name, input_types in ModuleInfo.module_inputs
    ]
    output_table = [
        [output_name, output_datatype_text(output_types)] for output_name, output_types in ModuleInfo.module_outputs
    ]
    optional_output_table = [
        [output_name, output_datatype_text(output_types)] for output_name, output_types in ModuleInfo.module_optional_outputs
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
            "(required) " if d.get("required", False) else "" + d.get("help", ""),
            format_option_type(d.get("type", str)),
        ]
        for (option_name, d) in sorted(ModuleInfo.module_options.items())
    ]

    filename = os.path.join(output_dir, "%s.rst" % module_path)
    with open(filename, "w") as output_file:
        # Make a page heading
        output_file.write(format_heading(0, "Pimlico module: %s" %
                                         (ModuleInfo.module_readable_name or ModuleInfo.module_type_name)))
        # Add a directive to mark this as the documentation for the py module that defines the Pimlico module
        output_file.write(".. py:module:: %s\n\n" % module_path)
        # Output a summary table of key information
        output_file.write("%s\n" % make_table(key_info))
        # Insert text from docstrings
        if info_doc is not None:
            output_file.write(trim_docstring(info_doc) + "\n")
        if module_info_doc is not None:
            output_file.write(trim_docstring(module_info_doc) + "\n")
        output_file.write("\n\n")
        output_file.write("".join("%s\n\n" % para for para in additional_paras))

        # Output a table of inputs
        output_file.write(format_heading(1, "Inputs"))
        if input_table:
            output_file.write("%s\n" % make_table(input_table, header=["Name", "Type(s)"]))
        else:
            output_file.write("No inputs\n")

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
    return ModuleInfo


def input_datatype_list(types):
    if type(types) is tuple:
        # This is a list of types
        return " or ".join(input_datatype_text(t) for t in types)
    else:
        # Just a single type
        return input_datatype_text(types)


def input_datatype_text(datatype):
    if isinstance(datatype, type) and issubclass(datatype, PimlicoDatatype):
        return ":class:`%s <%s>`" % (datatype.__name__, datatype.datatype_full_class_name())
    elif datatype.datatype_doc_info is not None:
        # Dynamic input type that gives us a name to use
        return datatype.datatype_doc_info
    else:
        # Dynamic datatype requirement with no custom string
        return ":class:`%s <%s.%s>`" % (type(datatype).__name__, type(datatype).__module__, type(datatype).__name__)


def output_datatype_text(datatype):
    if isinstance(datatype, DynamicOutputDatatype):
        # Use the datatype name given by the dynamic datatype and link to the class
        datatype_class = datatype.get_base_datatype_class()
        if datatype_class is not None:
            datatype_class_name = datatype_class.datatype_full_class_name()
        else:
            # Just link to the dynamic datatype class
            print datatype, type(datatype)
            datatype_class_name = "%s.%s" % (type(datatype).__module__, type(datatype).__name__)
        datatype_name = datatype.datatype_name or type(datatype).__name__
        return ":class:`%s <%s>`" % (datatype_name, datatype_class_name)
    else:
        return ":class:`%s <%s>`" % (datatype.__name__, datatype.datatype_full_class_name())


def generate_contents_page(modules, output_dir):
    module_names = [
        # If the module type defines a readable name, use that in the index
        (module.module_readable_name or module.module_package_name().partition("pimlico.modules.")[2],
         module.module_package_name())
        for module in modules
    ]
    with open(os.path.join(output_dir, "index.rst"), "w") as index_file:
        index_file.write("""\
{title}
.. toctree::
   :maxdepth: 1

   {list}
""".format(
            title=format_heading(0, "Core Pimlico modules"),
            list="\n   ".join("{name} <{module}>".format(name=name, module=module_package) for (name, module_package) in module_names)
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate module documentation RST files from the modules")
    parser.add_argument("output_dir", help="Where to put the .rst files")
    opts = parser.parse_args()

    output_dir = os.path.abspath(opts.output_dir)

    print "Sphinx %s" % __display_version__
    print "Pimlico module doc generator"
    print "Outputting module docs to %s" % output_dir

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    generate_docs(output_dir)
