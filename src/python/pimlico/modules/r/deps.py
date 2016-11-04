
from pimlico.core.dependencies.base import SystemCommandDependency


class RDependency(SystemCommandDependency):
    """
    Dependency on the R statistical programming language.

    Plain R dependency just checks that the R command is available. You may also specify a list of
    R libraries that you need and we will check whether they can be loaded with R's `library` command.

    """
    def __init__(self, libraries=[], **kwargs):
        super(RDependency, self).__init__("R", "R -h", **kwargs)
        self.libraries = libraries

    def problems(self):
        import subprocess

        probs = super(RDependency, self).problems()
        if len(probs) == 0 and len(self.libraries):
            # R itself can be loaded
            # Try loading required libraries
            for lib in self.libraries:
                proc = subprocess.Popen(["Rscript", "--vanilla", "-e", "library(%s)" % lib],
                                        stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                # Wait for the command to terminate
                stderr_out, stdout_out = proc.communicate()
                if proc.returncode > 0:
                    # There was an error
                    # UTF8 error messages on stdout? Yup
                    error_mess = " / ".join(stdout_out.decode("utf8").splitlines()[:-1])
                    probs.append("Could not load R library %s: %s" % (lib, error_mess))
        return probs

    def installation_instructions(self):
        # Check whether availability check failed because R isn't installed, or libraries
        if len(super(RDependency, self).problems()):
            return """\
Perform a system-wide installation of R. You may be able to do this using a
package manager, depending on your operating system. For example, on Ubuntu,
simply run:
  sudo apt-get install r-base

Instructions for manual installation can be found at:
  https://cran.r-project.org/doc/manuals/r-release/R-admin.html
"""
        else:
            return "R is installed, but the following problems were encountered loading required libraries: %s" \
                   % ", ".join(self.libraries)


r_dependency = RDependency()
