import os
from subprocess import Popen, PIPE, STDOUT

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        sources = self.info.get_input("sources")
        original_script_path = self.info.options["script"]

        if not os.path.exists(original_script_path):
            raise ModuleExecutionError("specified R script does not exist: %s" % original_script_path)

        # Load the R script we're going to run
        self.log.info("Loading R source from %s" % original_script_path)
        with open(original_script_path, "r") as f:
            r_source = f.read()

        # Make substitutions to allow inclusion of input paths from other modules and the output path
        for input_num, source in enumerate(sources):
            input_source_dir = source.data_dir if source.data_ready() else "INPUT%d_NOT_READY" % input_num
            r_source = r_source.replace("{{input%d}}" % input_num, input_source_dir)
        # Include the output dir as well
        output_dir = self.info.get_absolute_output_dir("output")
        # Make sure that this dir exists, so that the script (and we, below) can output to it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        r_source = r_source.replace("{{output}}", output_dir)

        # Write out the resulting R file ready for execution (and debugging)
        script_path = os.path.join(output_dir, "script.R")
        with open(script_path, "w") as f:
            f.write(r_source)
        self.log.info("Preprocessed R script stored as %s" % script_path)

        self.log.info("Running R script")
        output_lines = []
        print "##### R script execution begins #####"
        try:
            # Start the R script running
            cmd = ["Rscript", "--vanilla", script_path]
            process = Popen(cmd, stdout=PIPE, stderr=STDOUT,
                            universal_newlines=True, bufsize=1)
            outputter = iter(process.stdout.readline, "")
            for line in outputter:
                line = line.decode("utf-8")
                output_lines.append(line)
                print line.encode("utf-8"),

            process.stdout.close()
            return_code = process.wait()
            if return_code != 0:
                raise ModuleExecutionError("R failed: %s (executed: %s)" % (
                    output_lines[-1] if output_lines else "",
                    " ".join(cmd)
                ))
        finally:
            print "##### R script execution ends #####"
            # Whether or not the script succeeded, send all its output to a file
            output_path = self.info.get_output("output").absolute_path

            self.log.info("Writing R output to %s" % output_path)
            if not os.path.exists(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))

            with open(output_path, "w") as f:
                f.write((u"".join(output_lines)).encode("utf-8"))
