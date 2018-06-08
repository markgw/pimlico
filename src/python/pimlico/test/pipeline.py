# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Pipeline tests

Pimlico modules and datatypes cannot always be easily tested with unit tests and where they can it's
often not easy to work out how to write the tests in a neatly packaged way. Instead, modules can
package up tests in the form of a small pipeline that comes with a tiny dataset to use as input. The
pipeline can be run in a test environment, where software dependencies are installed and local
config is prepared to store output and so on.

This way of providing tests also has the advantage that modules at the same time provide a demo (or
several) of how to use them -- how pipeline config should look and what sort of input data to use.

"""
import traceback

from pimlico.utils.core import remove_duplicates

if __name__ == "__main__":
    from pimlico import install_core_dependencies
    install_core_dependencies()

import argparse
import os
import shutil

import sys

from pimlico import TEST_DATA_DIR, TEST_STORAGE_DIR
from pimlico.core.config import PipelineConfig, get_dependencies
from pimlico.core.dependencies.base import InstallationError
from pimlico.core.modules.base import collect_unexecuted_dependencies
from pimlico.core.modules.execute import check_and_execute_modules
from pimlico.core.modules.inputs import InputModuleInfo
from pimlico.datatypes.base import IterableCorpus
from pimlico.utils.logging import get_console_logger


class TestPipeline(object):
    def __init__(self, pipeline, run_modules, log):
        self.log = log
        self.requested_modules = run_modules
        self.pipeline = pipeline

        # Expand the list of requested modules to include any that they depend on
        modules = [self.pipeline[mod] for mod in self.requested_modules]
        self.to_run = remove_duplicates(self.requested_modules + [m.module_name for m in collect_unexecuted_dependencies(modules)])

    @staticmethod
    def load_pipeline(path, storage_root):
        """
        Load a test pipeline from a config file.

        Path may be absolute, or given relative to Pimlico test data directory (``PIMLICO_ROOT/test/data``)

        """
        if not os.path.isabs(path):
            path = os.path.join(TEST_DATA_DIR, path)
        if not os.path.exists(path):
            raise TestPipelineRunError("could not load test pipeline at '{}': file does not exist".format(path))
        # Set the local config paths to point to the (usually temporary) storage root we're using
        local_config = {
            "store": storage_root,
        }
        return PipelineConfig.load(path, override_local_config=local_config, only_override_config=True)

    def get_uninstalled_dependencies(self):
        deps = get_dependencies(self.pipeline, self.to_run, recursive=True)
        return [d for d in deps if not d.available(self.pipeline.local_config)]

    def test_all_modules(self):
        for module_name in self.to_run:
            self.log.info("Processing module '{}'".format(module_name))
            module = self.pipeline[module_name]
            if isinstance(module, InputModuleInfo):
                self.test_input_module(module_name)
            else:
                self.test_module_execution(module_name)

    def test_input_module(self, module_name):
        module = self.pipeline[module_name]
        # Check each output dataset
        # Typically there's only one, but we might as well deal with the case of multiple
        for output_name, dtype in module.module_outputs:
            dataset = module.get_output(output_name)
            if not dataset.data_ready():
                raise TestPipelineRunError("test of input dataset {}.{} failed: data not ready".format(
                    module.module_name, output_name
                ))
            # Handle special case of iterable corpora: check they can be iterated over
            if isinstance(dataset, IterableCorpus):
                try:
                    for doc_name, doc in dataset:
                        pass
                except Exception, e:
                    raise TestPipelineRunError("test of input dataset {}.{} failed: error while iterating over "
                                               "iterable corpus: {}".format(module.module_name, output_name, e))

    def test_module_execution(self, module_name):
        try:
            check_and_execute_modules(self.pipeline, [module_name], log=self.log)
        except Exception, e:
            raise TestPipelineRunError("error while running module '{}': {}".format(module_name, e))


def run_test_pipeline(path, module_names, log, no_clean=False):
    """
    Run a test pipeline, loading the pipeline config from a given path (which may be relative to the
    Pimlico test data directory) and running each of the named modules, including any of those
    modules' dependencies.

    Any software dependencies not already available that can be installed automatically will be
    installed in the current environment. If there are unsatisfied dependencies that can't be
    automatically installed, an error will be raised.

    If any of the modules name explicitly is an input dataset, it is loaded and data_ready() is checked.
    If it is an IterableCorpus, it is tested simply by iterating over the full corpus.

    """
    # Prepare the storage dir for pipeline output
    if not os.path.exists(TEST_STORAGE_DIR):
        raise TestPipelineRunError("test storage dir did not exist: {}".format(TEST_STORAGE_DIR))
    if not no_clean:
        clear_storage_dir()

    try:
        # Load the pipeline config
        try:
            pipeline = TestPipeline.load_pipeline(path, TEST_STORAGE_DIR)
            test_pipeline = TestPipeline(pipeline, module_names, log)
        except Exception, e:
            traceback.print_exc()
            raise TestPipelineRunError("could not load test pipeline {}: {}".format(path, e))

        # Check for uninstalled dependencies
        dep_problems = []
        for dep in test_pipeline.get_uninstalled_dependencies():
            # Make sure the dependency is still not available when we get to it
            if dep.available(pipeline.local_config):
                continue
            if dep.installable():
                log.info("Installing {}".format(dep.name))
                try:
                    dep.install(pipeline.local_config)
                except InstallationError, e:
                    dep_problems.append("Could not install dependency '{}': {}".format(dep.name, e))
            else:
                instructions = dep.installation_instructions()
                problems = dep.problems(pipeline.local_config)
                dep_problems.append("Dependency '{}' is not automatically installable. {}"
                                    "Install it manually before running this test{}".format(
                    dep.name,
                    "{}. ".format(", ".join(problems)) if len(problems) else "",
                    "\n{}".format(instructions) if instructions else ""
                ))
        if dep_problems:
            log.error("Cannot run test as there are dependency problems:")
            for dep_prob in dep_problems:
                log.error(dep_prob)
            raise TestPipelineRunError("unresolved dependency problems: see above for details")

        test_pipeline.test_all_modules()

    finally:
        if not no_clean:
            clear_storage_dir()


def run_test_suite(pipelines_and_modules, log, no_clean=False):
    """
    :param pipeline_and_modules: list of (pipeline, modules) pairs, where pipeline is a path to a config file and
        modules a list of module names to test
    """
    all_succeeded = True
    for path, module_names in pipelines_and_modules:
        log.info("Running test pipeline {}, modules {}".format(path, ", ".join(module_names)))
        try:
            run_test_pipeline(path, module_names, log, no_clean=no_clean)
        except TestPipelineRunError, e:
            log.error("Test failed: {}".format(e))
            all_succeeded = False
        else:
            log.info("Test succeeded")
    return all_succeeded


def clear_storage_dir():
    # Should remove any files or directories in there other than the README
    for filename in os.listdir(TEST_STORAGE_DIR):
        if filename != "README":
            path = os.path.join(TEST_STORAGE_DIR, filename)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)


class TestPipelineRunError(Exception):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline test runner")
    parser.add_argument("suite_file", help="CSV file in which each line contains a path to a pipeline config file "
                                           "(potentially relative to test data dir), then a list of modules to test")
    parser.add_argument("--no-clean", help="Do not clean up the storage directory after running tests. By default, "
                                           "all output from the test pipelines is deleted at the end",
                        action="store_true")
    opts = parser.parse_args()

    log = get_console_logger("Test")

    with open(opts.suite_file, "r") as f:
        rows = [row.split(",") for row in f.read().splitlines() if not row.startswith("#") and len(row.strip())]
    pipelines_and_modules = [(row[0].strip(), [m.strip() for m in row[1:]]) for row in rows]
    log.info("Running {} test pipelines".format(len(pipelines_and_modules)))

    all_succeeded = run_test_suite(pipelines_and_modules, log, no_clean=opts.no_clean)
    if all_succeeded:
        log.info("All tests completed successfully")
    else:
        log.error("Some tests did not complete successfully. See above for details")
    sys.exit(1 if all_succeeded else 0)
