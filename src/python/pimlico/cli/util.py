# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from cStringIO import StringIO
import sys
from traceback import format_exception_only


def module_number_to_name(pipeline, name):
    # Get the list of runable modules to select a name from
    modules = pipeline.get_module_schedule()
    # If the given name already identifies a module, don't do anything
    if name in modules:
        return name
    try:
        module_number = int(name) - 1
    except ValueError:
        # Wasn't an integer, just return the given value
        # If it's a non-existent module, an error will (presumably) be output when we try to load it
        # It could also be a special value, like "all", so we don't want to go raising errors here
        return name
    if not (0 <= module_number < len(modules)):
        raise ValueError("invalid module number: %d. The pipeline has %d modules" % (module_number+1, len(modules)))
    return modules[module_number]


def module_numbers_to_names(pipeline, names):
    """
    Convert module numbers to names, also handling ranges of numbers (and names) specified with "...". Any
    "..." will be filled in by the sequence of intervening modules.

    Also, if an unexpanded module name is specified for a module that's been expanded into multiple
    corresponding to alternative parameters, all of the expanded module names are inserted in place of the
    unexpanded name.

    """
    # Get the list of runable modules to select names from
    modules = pipeline.get_module_schedule()

    # Allow "..."s to be surrounded by spaces or not
    names = " ".join(names).replace("...", " ... ").split()

    module_names = []
    fill_next = False
    for name in names:
        if name == "...":
            fill_next = True
        else:
            # Convert numbers to names
            next_module = module_number_to_name(pipeline, name)
            # Check whether this is an unexpanded module name
            if next_module in pipeline.expanded_modules:
                # If we're adding multiple modules (expanded), make sure they're in the schedule order
                next_modules = [mod for mod in modules if mod in pipeline.expanded_modules[next_module]]
            else:
                next_modules = [next_module]

            if fill_next:
                # Both the previous and current modules must exist, i.e. not be some special value
                # Where we're not filling, we don't check this, but here it's necessary
                if len(module_names) == 0:
                    # No previous module: take range from start
                    previous_module = modules[0]
                    previous_module_num = 0
                    module_names.append(modules[0])
                else:
                    previous_module = module_names[-1]
                    if previous_module not in modules:
                        raise ValueError("could not find module '%s'. Can only use module ranges with explicit "
                                         "module names/numbers that exist in the pipeline" % previous_module)
                    previous_module_num = modules.index(previous_module)
                # Find the index of the end of the range
                for mod in next_modules:
                    if mod not in modules:
                        raise ValueError("could not find module '%s'. Can only use module ranges with explicit "
                                         "module names/numbers that exist in the pipeline" % mod)
                next_module_num = min(modules.index(mod) for mod in next_modules)
                # Check it's a valid range
                if previous_module_num >= next_module_num:
                    raise ValueError("invalid range of modules: %s (%d) ... %s (%d)" % (
                        previous_module, previous_module_num,
                        next_module, next_module_num
                    ))
                # Fill in the intervening modules
                module_names.extend(modules[previous_module_num+1:next_module_num])
                fill_next = False
            # Add this module, or modules
            module_names.extend(next_modules)
    return module_names


def format_execution_error(error):
    """
    Produce a string with lots of error output to help debug a module execution error.

    :param error: the exception raised (ModuleExecutionError or ModuleInfoLoadError)
    :return: formatted output
    """
    output = StringIO()
    print >>output, "\nDetails of error"
    print >>output,   "----------------"
    print >>output, "".join(format_exception_only(type(error), error)).strip("\n")
    if hasattr(error, "debugging_info") and error.debugging_info is not None:
        # Extra debugging information was provided by the exception
        print >>output, "\n## Further debugging info ##"
        print >>output, error.debugging_info.strip("\n")
    output_str = output.getvalue()

    if hasattr(error, "cause") and error.cause is not None:
        # Recursively print any debugging info on the cause exception
        output_str = "%s\n%s" % (output_str, format_execution_error(error.cause))
    return output_str


def print_execution_error(error):
    print >>sys.stderr, format_execution_error(error)
