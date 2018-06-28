# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import inspect
import threading

from pimlico.cli.debug import fmt_frame_info, output_stack_trace
from pimlico.old_datatypes import TarredCorpus


class Stepper(object):
    """
    Type that stores the state of the stepping process. This allows information and parameters to be
    passed around through the process and updated as we go. For example, if particular type of output
    is disabled by the user, a parameter can be updated here so we know not to output it later.

    """
    def __init__(self):
        self.executing = False
        self.disabled_categories = []
        self.interaction_lock = threading.Lock()


def enable_step_for_pipeline(pipeline):
    """
    Prepares a pipeline to run in step mode, modifying modules and wrapping methods to supply the extra
    functionality.

    This approach means that we don't have to consume extra computation time checking whether step mode
    is enabled during normal runs.

    :param pipeline: instance of PipelineConfig
    """
    # Once the stepper has been assigned, that in itself acts as an indication that we're running in step mode
    # It also stores parameters and state as required
    pipeline._stepper = Stepper()

    # Wrap all get_input() methods of module infos
    for module_name, module in pipeline.module_infos.items():
        # Check each of the outputs to see whether it's a tarred corpus
        wrap_output_names = []
        for output_name in module.output_names:
            dtype = module.get_output(output_name)
            if isinstance(dtype, TarredCorpus):
                # Wrap some of the datatype's methods
                wrap_output_names.append(output_name)

        # We have to wrap the datatype by wrapping the instantiate_output_datatype() method, which is always
        # used to instantiate it
        module.instantiate_output_datatype = instantiate_output_datatype_decorator(
            module.instantiate_output_datatype, module_name, wrap_output_names, pipeline._stepper
        )

        module.get_input = get_input_decorator(module.get_input, module_name, pipeline._stepper)


def instantiate_output_datatype_decorator(instantiate_output_datatype, module_name, output_names, stepper):
    def wrapped_method(output_name, *args, **kwargs):
        # First call the normal method
        dtype = instantiate_output_datatype(output_name, *args, **kwargs)
        # Only wrap particular outputs
        if output_name in output_names:
            # Wrap the produced datatype
            wrap_tarred_corpus(dtype, module_name, output_name, stepper)
        return dtype

    return wrapped_method


def wrap_tarred_corpus(dtype, module_name, output_name, stepper):
    dtype.archive_iter = archive_iter_decorator(dtype.archive_iter, module_name, output_name, stepper)


def archive_iter_decorator(archive_iter, module_name, output_name, stepper):
    def wrapped_archive_iter(*args, **kwargs):
        this_iter_category = "%s.%s-iter" % (module_name, output_name)
        general_iter_category = "corpus_iter"
        start_iter_category = "start:%s" % this_iter_category
        general_start_iter_category = "start:%s" % general_iter_category
        iter_name = "output '%s' from '%s'" % (output_name, module_name)

        # Output a message at the start of iteration
        f = inspect.stack()[2][0]
        f_info = inspect.getframeinfo(f)
        option_message(
            ["Starting iteration of %s using archive_iter()" % iter_name, fmt_frame_info(f_info)],
            stepper, category=(general_start_iter_category, start_iter_category),
        )

        for archive_name, doc_name, doc in archive_iter(*args, **kwargs):
            # Allow user to opt out of showing this iterator, or showing any iterator
            if stepper.executing and this_iter_category not in stepper.disabled_categories \
                    and general_iter_category not in stepper.disabled_categories:
                # Check where we're being called from
                f = inspect.stack()[2][0]
                f_info = inspect.getframeinfo(f)
                # Format the doc simply by converting to a string
                full_doc_str = str(doc)
                short_doc_str = full_doc_str
                # Abbreviate output for the first display
                if len(short_doc_str) > 200:
                    short_doc_str = "%s..." % short_doc_str[:200]
                # Don't allow multiple lines
                if short_doc_str.count("\n") > 0:
                    short_doc_str = short_doc_str.partition("\n")[0]

                message = [
                    "Document %s/%s from %s" % (archive_name, doc_name, iter_name),
                    # Output info about where we were called from
                    fmt_frame_info(f_info),
                    short_doc_str,
                ]

                # Allow the full doc to be displayed on request
                def _display_full():
                    print full_doc_str

                option_message(
                    message, stepper, options=[("full", "show full doc", _display_full)],
                    category=(general_iter_category, this_iter_category),
                )
            # Yield exactly what the original iterator would have done
            yield archive_name, doc_name, doc

    return wrapped_archive_iter


def get_input_decorator(get_input, module_name, stepper):
    """
    Decorator to wrap a module info's get_input() method so when know where inputs are being used.

    """
    def wrapped_get_input(*args, **kwargs):
        # Only apply this if execution has begun, otherwise we output load of stuff during dependency checking
        if stepper.executing and "get_input" not in stepper.disabled_categories:
            message = []
            # Output a message to say the data was retrieved
            message.append("Retrieved input '%s' to module '%s'" % (args[0], module_name))
            # Check where we're being called from
            f = inspect.stack()[2][0]
            f_info = inspect.getframeinfo(f)
            # Output info about where we were called from
            message.append(fmt_frame_info(f_info))

            # Make the actual wrapped call to get the datatype
            dtype = get_input(*args, **kwargs)
            # Try outputting the datatype itself, which should generally show something short
            dtype_str = str(dtype)
            # Limit the length of the output
            if len(dtype_str) > 200:
                dtype_str = "%s..." % dtype_str[:200]
                # Don't allow multiple lines
            if dtype_str.count("\n") > 0:
                dtype_str = dtype_str.partition("\n")[0]
            message.append(dtype_str)
            # Display the message
            option_message(message, stepper, category="get_input()")

            return dtype
        else:
            return get_input(*args, **kwargs)

    return wrapped_get_input


def option_message(message_lines, stepper, options=None, stack_trace_option=True, category=None):
    if category is not None:
        if type(category) is not tuple:
            category = (category,)
        if any(c in stepper.disabled_categories for c in category):
            # This type of output has been disabled, don't output anything
            return

    # Avoid threading problems with multiple messages being displayed at once by hold a lock for this whole process
    with stepper.interaction_lock:
        print
        # Show message, indenting all but first line
        print "\n    ".join(message_lines)

        if options is None:
            options = []
        if stack_trace_option:
            # Get a frame corresponding to the place where this function was called
            f = inspect.stack()[2][0]
            options.append(("tr", "full stack trace", lambda: output_stack_trace(f)))

        if category is not None:
            # Add an option to disable this category of output in future
            for cat in category:
                trigger_len = 1
                while "x%s" % cat[:trigger_len] in [t for (t, __, __) in options]:
                    trigger_len += 1

                def _disable():
                    stepper.disabled_categories.append(cat)
                    return True

                options.append(("x%s" % cat[:trigger_len], "stop outputting %s messages" % cat, _disable))
        # Check whether there's a default option
        if not any(trigger is None for (trigger, __, __) in options):
            options.append((None, "continue", lambda: True))

        options = [
            (trigger.lower() if trigger is not None else None,
             "%s=%s" % (trigger if trigger is not None else "<enter>", message), fn)
            for (trigger, message, fn) in options
        ]
        option_fns = dict((trigger, fn) for (trigger, message, fn) in options)

        while True:
            choice = raw_input("%s: " % ", ".join(message for (trigger, message, fn) in options)).lower().strip("\n ")
            if choice in option_fns:
                # Run the callback for this option
                exit = option_fns[choice]()
                if exit:
                    break
            else:
                if len(choice) == 0 and None in option_fns:
                    # If there's a default option, use it
                    exit = option_fns[None]()
                    if exit:
                        break
                # Go round again
                print "Option '%s' not recognized" % choice
        print