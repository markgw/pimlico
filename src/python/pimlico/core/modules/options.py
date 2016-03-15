
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

    def _fn(string):
        if string not in options:
            raise ValueError("%s is not a valid value%s. Valid choices: %s" % (string, name_text, ", ".join(options)))
        else:
            return string
    return _fn


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
            raise ModuleOptionParseError("invalid option for %s module: '%s'" % (module_type_name, name))
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
