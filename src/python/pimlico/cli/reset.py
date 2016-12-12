from pimlico.utils.core import remove_duplicates


def reset_module(pipeline, opts):
    if "all" in opts.modules:
        # Reset every module, one by one
        print "Resetting execution state of all modules"
        pipeline.reset_all_modules()
    else:
        module_names = opts.modules
        if opts.no_deps:
            dependent_modules = []
        else:
            # Check for modules that depend on these ones: they should also be reset, since their input data will be rebuilt
            dependent_modules = remove_duplicates(sum(
                (pipeline.get_dependent_modules(module_name, recurse=True) for module_name in module_names), []
            ))
            dependent_modules = [m for m in dependent_modules if m not in module_names]
            # Don't bother to include ones that haven't been executed anyway
            dependent_modules = [m for m in dependent_modules if pipeline[m].status != "UNEXECUTED"]
            if len(dependent_modules) > 0:
                # There are additional modules that we should reset along with these,
                # but check with the user in case they didn't intend that
                print "The following modules depend on %s. Their execution state will be reset too if you continue." % \
                      ", ".join(module_names)
                print "  %s" % ", ".join(dependent_modules)
                answer = raw_input("Do you want to continue? [y/N] ")
                if answer.lower() != "y":
                    print "Cancelled"
                    return

        for module_name in module_names + dependent_modules:
            print "Resetting execution state of module %s" % module_name
            module = pipeline[module_name]
            module.reset_execution()