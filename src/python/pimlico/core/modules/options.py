# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Utilities and type processors for module options.

"""
from builtins import str
from past.builtins import basestring

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


def opt_type_example(example_text):
    """
    Decorate to add an example value to function that are designed to be used as
    module option processors. The given text will be used in module docs as an example
    of how to specify the option in a config file.

    """
    def _wrap(fn):
        fn._opt_type_example = example_text
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
    @opt_type_help(options[0])
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
    _fn.list_item_type = item_type
    return _fn


# For convenience, name the common case where the values are not parsed at all
comma_separated_strings = comma_separated_list()


@opt_type_help("JSON string")
def json_string(string):
    try:
        return json.loads(string)
    except ValueError as e:
        raise ValueError("error parsing JSON string: {}".format(e))


@opt_type_help("JSON dict")
def json_dict(string):
    """JSON dicts, with or without {}s"""
    string = string.strip()
    if string[0] != "{":
        # {}s weren't included
        string = "{%s}" % string

    try:
        return json.loads(string)
    except ValueError as e:
        raise ValueError("error parsing JSON string: {}".format(e))


def _enhanced_int(val):
    """
    Used as a replacement for the builtin int for converting strings to ints.

    Allows spaces and commas to be included in ints to make them more readable.

    Also allows the use of suffixes ``k`` and ``m``, for thousands and millions
    """
    val = val.replace(" ", "")
    val = val.replace(",", "")
    if val.lower().endswith("k"):
        val = "{}000".format(val[:-1])
    elif val.lower().endswith("m"):
        val = "{}000000".format(val[:-1])
    return int(val)


def process_module_options(opt_def, opt_dict, module_type_name):
    """
    Utility for processing runtime module options. Called from module base class.

    Also used when loading a dataset's datatype from datatype options specified in a config file.

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
            type_conv = opt_config["type"]
            if type_conv is int:
                # Drop-in replacement for int to allow for more readable formatting
                type_conv = _enhanced_int
            try:
                value = type_conv(value)
            except Exception as e:
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
