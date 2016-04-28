"""
Basic setup of Pimlico.
This is provided primarily so that the docs can be built on the ReadTheDocs server and can import all the
code, including basic dependencies.

"""
# Just call make to get the basic dependencies and set up in place
import os
from subprocess import call
call(["make"], cwd=os.path.join("lib/python"), shell=True)

"""
import os
from distutils.command.install import install as _install
from setuptools import find_packages, setup


def _post_install(dir):
    from subprocess import call
    call(["make"], cwd=os.path.join(dir, "lib", "python"))


class install(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,), msg="Running post install task to install basic libs")


setup(
    name="Pimlico",
    version="0.1",
    author="Mark Granroth-Wilding",
    package_dir={"pimlico": "src/python/pimlico"},
    packages=find_packages("./src/python"),
    package_data={
        "": ["lib/*", "bin/*", "models/*", "examples/*", "build/*"]
    },
    include_package_data=True,
    #cmdclass={'install': install},
)
"""
