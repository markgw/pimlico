import os

from pip._vendor.distlib._backport import shutil

from pimlico.cli.subcommands import PimlicoCLISubcommand


class CleanCmd(PimlicoCLISubcommand):
    command_name = "clean"
    command_help = "Remove all module directories that do not correspond to a module in the pipeline " \
                   "in all storage locations. This is useful when modules have been renamed or removed and output " \
                   "directories have got left behind. Note that it is specific to the selected variant"

    def run_command(self, pipeline, opts):
        to_clean = []
        for root_dir in pipeline.get_storage_roots():
            if os.path.exists(root_dir):
                for dirname in os.listdir(root_dir):
                    if os.path.isdir(os.path.join(root_dir, dirname)):
                        # Check whether this dir name corresponds to a module in the pipeline
                        if dirname not in pipeline:
                            # No module called by this name: this dir probably shouldn't be here
                            to_clean.append(os.path.join(root_dir, dirname))

        if len(to_clean) == 0:
            print "Found no directories to clean"
        else:
            print "Directories that do not seem to correspond to pipeline modules:"
            print "\n".join(" - %s" % path for path in to_clean)
            print
            answer = raw_input("Do you want to remove these directories? [y/N]: ")
            if answer.lower() == "y":
                for path in to_clean:
                    shutil.rmtree(path)
                print "All unnecessary data directories cleaned up"
            else:
                print "Cancelled"
