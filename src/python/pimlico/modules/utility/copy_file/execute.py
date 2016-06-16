import shutil

import os

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # Locate the input file(s)
        input_files = self.info.get_input("source")
        # Work out where to put it
        target_dir = self.info.options["target_dir"]
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        target = target_dir
        if len(input_files) == 1 and self.info.options["target_name"] is not None:
            # Use a new name if one was given
            target = os.path.join(target_dir, self.info.options["target_name"])

        for input_file in input_files:
            source_path = input_file.absolute_path
            # Copy the file
            shutil.copy(source_path, target)
            self.log.info("Copied %s to %s" % (os.path.basename(source_path), target_dir))
