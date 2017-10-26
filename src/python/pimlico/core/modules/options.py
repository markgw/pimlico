# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Utilities and type processors for module options.

"""
import json

from pimlico.utils.strings import sorted_by_similarity


def opt_type_help(help_text):
    """
    Decorator to add help text to functions that are designed to be used as module option processors. The
    help text will be used to describe the type in documentation.

    """
    def _wrap(fn):
        fn.option_help_text = help_text
        return fn
    return _wrap


def format_option_type(t):
    if hasattr(t, "option_help_text"):
        # Help text added by opt_type_help decorator
        return t.option_help_text
    elif t is str:
        return "string"
    elif t is int:
        return "int"
    elif t is float:
        return "float"
    else:
        return str(t)


@opt_type_help("bool")
def str_to_bool(string):
    """
    Convert a string value to a boolean in a sensible way. Suitable for specifying booleans as options.

    :param string: input string
    :return: boolean value
    """
    if isinstance(string, basestring) and string.lower() in ["0", "f", "false", "n", "no"]:
        return False
    else:
        return bool(string)


def choose_from_list(options, name=None):
    """
    Utility for option processors to limit the valid values to a list of possibilities.

    """
    name_text = " for option %s" % name if name is not None else ""
    if len(options) == 0:
        help_text = "(no valid values)"
    elif len(options) == 1:
        help_text = "'%s'" % options[0]
    else:
        help_text = "%s or '%s'" % (", ".join("'%s'" % o for o in options[:-1]), options[-1])

    @opt_type_help(help_text)
    def _fn(string):
        if string not in options:
            raise ValueError("%s is not a valid value%s. Valid choices: %s" % (string, name_text, ", ".join(options)))
        else:
            return string
    return _fn


def comma_separated_list(item_type=str, length=None):
    """
    Option processor type that accepts comma-separated lists of strings. Each value is then parsed according to the
    given item_type (default: string).

    """
    @opt_type_help("comma-separated list of %s%ss" % ("" if length is None else "%d " % length, format_option_type(item_type)))
    def _fn(string):
        if string.strip():
            result = [
                item_type(val.strip()) for val in string.split(",")
            ]
        else:
            result = []
        if length is not None and len(result) != length:
            raise ValueError("list must contain %d values, got %d" % (length, len(result)))
        return result
    return _fn


# For convenience, name the common case where the values are not parsed at all
comma_separated_strings = comma_separated_list()


@opt_type_help("JSON string")
def json_string(string):
    try:
        return json.loads(string)
    except ValueError, e:
        raise ValueError("error parsing JSON string: {}".format(e))


def process_module_options(opt_def, opt_dict, module_type_name):
    """
    Utility for processing runtime module options. Called from module base class.

    :param opt_def: dictionary defining available options
    :param opt_dict: dictionary of option values
    :param module_type_name: name for error output
    :return: dictionary of processed options

    """
    options = {}
    for name, value in opt_dict.items():
        if name not in opt_def:
            # Look for similar option names to suggest
            available_opts = sorted_by_similarity(opt_def.keys(), name)
            raise ModuleOptionParseError("invalid option for %s module: '%s'. Available options: %s" %
                                         (module_type_name, name, ", ".join("'%s'" % opt for opt in available_opts)))
        # Postprocess the option value
        opt_config = opt_def[name]
        if "type" in opt_config:
            try:
                value = opt_config["type"](value)
            except Exception, e:
                raise ModuleOptionParseError("error processing option value '%s' for %s option in %s module: %s" %
                                             (value, name, module_type_name, e))
            options[name] = value
        else:
            # Just use string value
            options[name] = value

    # Check for unspecified options
    for opt_name, opt_config in opt_def.items():
        # Look for options we've not already processed
        if opt_name not in options:
            if "default" in opt_config:
                # If a default was specified, use it
                options[opt_name] = opt_config["default"]
            elif "required" in opt_config and opt_config["required"]:
                # If the option was required, complain
                raise ModuleOptionParseError("%s option is required for %s module, but was not given" %
                                             (opt_name, module_type_name))
            else:
                # Otherwise, include as None, so the options are all in the dict
                options[opt_name] = None
    return options


class ModuleOptionParseError(Exception):
    pass
