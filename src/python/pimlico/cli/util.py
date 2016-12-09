

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


def module_numbers_to_names(pipeline, names):
    """
    Convert module numbers to names, also handling ranges of numbers (and names) specified with "...". Any
    "..." will be filled in by the sequence of intervening modules.

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
                if next_module not in modules:
                    raise ValueError("could not find module '%s'. Can only use module ranges with explicit "
                                     "module names/numbers that exist in the pipeline" % next_module)
                next_module_num = modules.index(next_module)
                # Check it's a valid range
                if previous_module_num >= next_module_num:
                    raise ValueError("invalid range of modules: %s (%d) ... %s (%d)" % (
                        previous_module, previous_module_num,
                        next_module, next_module_num
                    ))
                # Fill in the intervening modules
                module_names.extend(modules[previous_module_num+1:next_module_num])
                fill_next = False
            # Add this module
            module_names.append(next_module)
    return module_names
