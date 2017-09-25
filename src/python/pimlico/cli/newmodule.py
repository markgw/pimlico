import os

from pimlico import PROJECT_ROOT
from pimlico.cli.subcommands import PimlicoCLISubcommand


class NewModuleCmd(PimlicoCLISubcommand):
    command_name = "newmodule"
    command_help = "Interactive tool to create a new module type, generating a skeleton for the module's code. " \
                   "Currently only works for certain module types. May be extended in future to help with " \
                   "creating a broader range of sorts of modules"
    command_desc = "Create a new module type"

    def run_command(self, pipeline, opts):
        # We assume that the first location given in the pipeline's python_path variable is where the project's
        # main custom code lives and create the new code there
        python_paths = pipeline.pipeline_config["python_path"].split(":")
        if len(python_paths) == 0:
            print "Could not determine a location for creating the new module code, since the pipeline does not " \
                  "specify a 'python_path' variable"
            path = ask("Enter a base path for your custom Pimlico code (may be relative to project root): ")
            if os.path.isabs(path):
                code_root = path
            else:
                code_root = os.path.abspath(os.path.join(PROJECT_ROOT, path))
        else:
            code_root = os.path.abspath(python_paths[0])
        print "New code will live in %s" % code_root
        # Make sure the root dir exists
        if not os.path.exists(code_root):
            os.makedirs(code_root)

        module_path = ask("Enter name for new module (full python path, e.g. 'mypackage.modules.mymodule'): ")
        module_root_dir = os.path.join(code_root, *(module_path.split(".")))
        print "Module code will be created in %s" % module_root_dir
        # Create Python directories as necessary to create the new module's directory
        if os.path.exists(module_root_dir):
            print "Module directory already exists: not creating any code, so we don't overwrite existing code"
            return

        rt = code_root
        for prt in module_path.split("."):
            rt = os.path.join(rt, prt)
            if not os.path.exists(rt):
                os.mkdir(rt)
            if not os.path.exists(os.path.join(rt, "__init__.py")):
                # Touch the file to create it
                with open(os.path.join(rt, "__init__.py"), "w"):
                    pass

        imports = []

        # Work out what category of module we're creating
        print "\nSelect a category of module to create:"
        print " 1. Generic"
        print " 2. Document map module"
        # In future, you probably want to add, e.g. filter modules, multistage modules, ...
        module_category = int(ask("Category: "))
        assert module_category in [1, 2]

        # Ask some questions that apply to all module categories
        module_type_name = module_path.split(".")[-1]
        module_readable_name = ask("Enter readable name "
                                   "(short description, e.g. 'Take numeric input and multiply it'): ")

        print "\nCreate module options"
        print "====================="
        module_options = []
        option_egs = []
        while True:
            option_name = ask("Option name (blank to stop creating options): ")
            if " " in option_name:
                print "Option name cannot include spaces"
                continue
            elif len(option_name) == 0:
                break
            # Ask questions to guide the user through defining the module option
            option_def = []

            print "Choose one of the standard option types, or edit the "
            print "generated code afterwards to use a different one"
            print " 1. string"
            print " 2. integer"
            print " 3. float"
            print " 4. boolean"
            print " 5. choice from list of possible values"
            print " 6. comma-separated list"
            option_type_choice = int(ask("Option type: "))
            # String is the default, so we don't need to specify a type
            if option_type_choice != 1:
                if option_type_choice == 2:
                    option_type = "int"
                    option_eg = "10"
                elif option_type_choice == 3:
                    option_type = "float"
                    option_eg = "1.5"
                elif option_type_choice == 4:
                    option_type = "str_to_bool"
                    option_eg = "T"
                    imports.append("from pimlico.core.modules.options import str_to_bool")
                elif option_type_choice == 5:
                    imports.append("from pimlico.core.modules.options import choose_from_list")
                    print "Specifying values (strings, unquoted) to choose from:"
                    choices = []
                    while True:
                        next_value = ask("Next value (blank to stop): ", strip_space=False)
                        if len(next_value):
                            choices.append('"%s"' % next_value)
                        else:
                            break
                    option_type = 'choose_from_list([%s], name="%s")' % (", ".join(choices), option_name)
                    option_eg = choices[0]
                elif option_type_choice == 6:
                    print "What type of values are in the list? (Customize afterwards if you need other types)"
                    print " 1. string"
                    print " 2. integer"
                    print " 3. float"
                    print " 4. other"
                    option_list_type_choice = int(ask("Type: "))
                    if option_list_type_choice == 1:
                        imports.append("from pimlico.core.modules.options import comma_separated_strings")
                        option_type = "comma_separated_strings"
                        option_eg = "x,y,z"
                    elif option_list_type_choice == 2:
                        imports.append("from pimlico.core.modules.options import comma_separated_list")
                        option_type = "comma_separated_list(item_type=int)"
                        option_eg = "1,2,3"
                    elif option_list_type_choice == 3:
                        imports.append("from pimlico.core.modules.options import comma_separated_list")
                        option_type = "comma_separated_list(item_type=float)"
                        option_eg = "1.2,5.4,3.9"
                    else:
                        imports.append("from pimlico.core.modules.options import comma_separated_list")
                        option_type = "comma_separated_list(item_type=???)  # TODO Put your type in here"
                        option_eg = "x,y,z"
                else:
                    print "Unknown type"
                    continue
                option_def.append(("type", option_type))
            else:
                option_eg = "something"

            print "Describe the option, so the module's users understand what it does"
            option_help = ask("Description: ")
            if len(option_help):
                # Escape any double quotes
                option_help = option_help.replace('"', '\\"')
                # Apply word-wrap to help text so the code isn't messy
                if len(option_help) > 55:
                    rmng = option_help
                    help_lines = []
                    while len(rmng):
                        if " " not in rmng:
                            # No spaces, just split
                            line = rmng[:55]
                            rmng = rmng[55:]
                        else:
                            line = rmng[:54].rpartition(" ")[0] + " "
                            rmng = rmng[len(line):]
                        help_lines.append(line)
                    option_help = '"%s"' % '"\n                     "'.join(help_lines)
                else:
                    option_help = '"%s"' % option_help
                option_def.append(("help", option_help))

            print "You can give the option a default value."
            print "Specify as Python code (i.e. quote it if it's a string)."
            print "Leave blank to use None as the default"
            option_default = ask("Default value: ")
            if option_default:
                option_def.append(("default", option_default))

            option_egs.append((option_name, option_eg))

            # Put together the option definition as a dictionary
            module_options.append('        "%s": {\n%s\n        },' % (
                option_name,
                "\n".join('            "%s": %s,' % (name, df) for (name, df) in option_def)
            ))
            print

        template_data = {
            "module_type_name": module_type_name,
            "module_readable_name": module_readable_name,
            "module_options": "\n".join(module_options),
        }

        if module_category == 1:
            imports.append("from pimlico.core.modules.base import BaseModuleInfo")
            template = GENERIC_TEMPLATE
        else:
            imports.append("from pimlico.core.modules.map import DocumentMapModuleInfo")
            template = DOC_MAP_TEMPLATE

        template_data["imports"] = "\n".join(imports)

        # Render the template
        info_code = template.format(**template_data)
        # Output it to the info file
        info_path = os.path.join(module_root_dir, "info.py")
        with open(info_path, "w") as f:
            f.write(info_code)

        #######
        # Now create the executor
        exec_template_data = {}
        if module_category == 1:
            # This is a simple template
            exec_template = GENERIC_EXEC_TEMPLATE
        else:
            exec_template = DOC_MAP_EXEC_TEMPLATE
            exec_imports = []

            print "Several types of document map module are available:"
            print " 1. Multiprocessing: documents may be processed in parallel (using multiprocessing), by specifying "
            print "    --processes at runtime"
            print " 2. Threaded: similar, but parallelization is implemented using Python's threading package. This "
            print "    will not take advantage of multiple processors or system-level parallelism, but is useful, for "
            print "    example, if your process function calls background processes to do the legwork"
            print " 3. Single-process: do not parallelize, even if --processes is set at runtime. Use where you know "
            print "    that things will go wrong if documents are processed in parallel"
            map_type_choice = int(ask("Choose a map module type: "))

            if map_type_choice == 1:
                exec_imports.append("from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory")
                exec_template_data["factory"] = "multiprocessing_executor_factory"
            elif map_type_choice == 2:
                exec_imports.append("from pimlico.core.modules.map.threaded import threading_executor_factory")
                exec_template_data["factory"] = "threading_executor_factory"
            else:
                exec_imports.append("from pimlico.core.modules.map.singleproc import single_process_executor_factory")
                exec_template_data["factory"] = "single_process_executor_factory"

            exec_template_data["imports"] = "\n".join(exec_imports)

        # Render the template
        exec_code = exec_template.format(**exec_template_data)
        # Output it to the execute file
        exec_path = os.path.join(module_root_dir, "execute.py")
        with open(exec_path, "w") as f:
            f.write(exec_code)

        # Prepare an example of the config code
        config_eg = CONFIG_TEMPLATE.format(
            module_path=module_path,
            option_egs="\n".join("%s=%s" % (name, eg) for (name, eg) in option_egs)
        )

        print "\nModule created"
        print "=============="
        print " 1. Edit the module metedata in %s" % info_path
        print " 2. Write the module's execution code in %s" % exec_path
        print " 3. Use the module in your pipeline with something like this:"
        print
        print config_eg



def ask(prompt, strip_space=True):
    strp = "\n " if strip_space else "\n"
    print
    val = raw_input("  %s" % prompt).strip(strp)
    print
    return val


GENERIC_TEMPLATE = """\
\"\"\"
.. todo::

   Document module {module_type_name}

\"\"\"
{imports}


class ModuleInfo(BaseModuleInfo):
    module_type_name = "{module_type_name}"
    module_readable_name = "{module_readable_name}"
    module_inputs = [
        # TODO Define module inputs here as:
        # ("input_name", InputTypeClass),
    ]
    module_outputs = [
        # TODO Define module outputs here as:
        # ("output_name", OutputTypeClass),
    ]
    module_options = {{
{module_options}
    }}

"""


DOC_MAP_TEMPLATE = """\
\"\"\"
.. todo::

   Document module {module_type_name}

\"\"\"
{imports}


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "{module_type_name}"
    module_readable_name = "{module_readable_name}"
    module_inputs = [
        # TODO Define module inputs here as:
        # ("input_name", InputTypeClass),
        # At least one should be a sub-type of IterableCorpus
    ]
    module_outputs = [
        # TODO Define module outputs here as:
        # ("output_name", OutputTypeClass),
        # At least one should be a sub-type of IterableCorpus
    ]
    module_options = {{
{module_options}
    }}

    def get_writer(self, output_name, output_dir, append=False):
        # TODO Return an appropriate writer instance for each output
        raise NotImplementedError("writer creation not implemented for {module_type_name}")

"""


GENERIC_EXEC_TEMPLATE = """\
from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # TODO Write execution code here
        # The metadata, options, etc are available through the module info instance in self.info
        pass

"""


DOC_MAP_EXEC_TEMPLATE = """\
from pimlico.core.modules.map import skip_invalid
{imports}


# Remove skip_invalid if you want to process invalid documents, rather than just pass them through
@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # TODO Define the actual processing that the module does on each doc
    # Access anything initialized per worker via the worker
    # Access anything initialized just once (preprocess_fn) via worker.executor
    # Access the module info instance (for options, etc) in worker.info

    return  # TODO Return result to be passed to the output writer


# You might also want to specify preprocess_fn, postprocess_fn, worker_set_up_fn, worker_tear_down_fn
ModuleExecutor = {factory}(process_document)

"""


CONFIG_TEMPLATE = """\
[my_instance_name]
type={module_path}
# Once you've defined your module inputs, specify where each comes from with:
input_NAME=module_name.output_name
{option_egs}
"""
