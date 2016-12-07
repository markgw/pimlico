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
    return modules[module_number]