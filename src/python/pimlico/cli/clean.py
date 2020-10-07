# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function
from builtins import input

import os

import shutil

from pimlico.cli.subcommands import PimlicoCLISubcommand


class CleanCmd(PimlicoCLISubcommand):
    """
    Cleans up module output directories that have got left behind.

    Often, when developing a pipeline incrementally, you try out some modules, but then remove them, or
    rename them to something else. The directory in the Pimlico output store that was created to contain
    their metadata, status and output data is then left behind and no longer associated with any module.

    Run this command to check all storage locations for such directories. If it finds any, it prompts you
    to confirm before deleting them. (If there are things in the list that don't look like they were left
    behind by the sort of things mentioned above, don't delete them! I don't want you to lose your precious
    output data if I've made a mistake in this command.)

    Note that the operation of this command is specific to the loaded pipeline variant. If you have multiple
    variants, make sure to select the one you want to clean with the general `--variant` option.

    """
    command_name = "clean"
    command_help = "Remove all module directories that do not correspond to a module in the pipeline " \
                   "in all storage locations. This is useful when modules have been renamed or removed and output " \
                   "directories have got left behind. Note that it is specific to the selected variant"
    command_desc = "Remove all module output directories that do not correspond to a module in the pipeline"

    def run_command(self, pipeline, opts):
        to_clean = set()
        for store_name, root_dir in pipeline.storage_locations:
            if os.path.exists(root_dir):
                for dirname in os.listdir(root_dir):
                    if os.path.isdir(os.path.join(root_dir, dirname)):
                        # Check whether this dir name corresponds to a module in the pipeline
                        if dirname not in pipeline:
                            # No module called by this name: this dir probably shouldn't be here
                            to_clean.add(os.path.join(root_dir, dirname))

        if len(to_clean) == 0:
            print("Found no directories to clean")
        else:
            print("Directories that do not seem to correspond to pipeline modules:")
            print("\n".join(" - %s" % path for path in to_clean))
            print()
            answer = input("Do you want to remove these directories? [y/N]: ")
            if answer.lower() == "y":
                for path in to_clean:
                    shutil.rmtree(path)
                print("All unnecessary data directories cleaned up")
            else:
                print("Cancelled")
