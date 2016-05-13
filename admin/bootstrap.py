"""
Bootstrapping script that create a basic Pimlico setup, either for an existing config file, or for a new project.

One use of this is to distribute it with your Pimlico project code. You don't need to distribute Pimlico itself
with your project, since it can be downloaded later. Just distribute a directory tree containing your config files,
your own code and this Python script, which will fetch everything else it needs.

Another use is to get a whole new project up and running. Simply download this script, place it in your project
directory, and call `python bootstrap.py`.

"""
import sys
import os


def start_new_project(directory):
    # TODO Get Pimlico
    # TODO Create basic config file template
    pass


def find_config_value(config_path, key, start_in_pipeline=False):
    with open(config_path, "r") as f:
        in_pipeline = start_in_pipeline

        for line in f:
            line = line.strip("\n ")
            if in_pipeline and line:
                # Look for the required key in the pipeline section
                line_key, __, line_value = line.partition("=")
                if line_key.strip() == key:
                    return line_value.strip()
            elif line.startswith("["):
                # Section heading
                # Start looking for keys if we're in the pipeline section
                in_pipeline = line.strip("[]") == "pipeline"
            elif line.startswith("%% INCLUDE"):
                # Found include directive: follow into the included file
                filename = line[10:].strip()
                # Get filename relative to current config file
                filename = os.path.join(os.path.dirname(config_path), filename)
                found_value = find_config_value(filename, key, start_in_pipeline=in_pipeline)
                if found_value is not None:
                    return found_value
    # Didn't find the key anywhere
    return


if __name__ == "main":
    args = sys.argv[1:]
    current_dir = os.path.abspath(os.path.dirname(__file__))

    if len(args) == 0:
        # Starting a new project in the current directory
        start_new_project(current_dir)
    else:
        config_file = os.path.abspath(args[0])
        # Check the config file to find the version of Pimlico we need
        version = find_config_value(config_file, "release")
        # TODO Get Pimlico
