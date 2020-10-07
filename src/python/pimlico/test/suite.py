# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html


if __name__ == "__main__":
    from pimlico import install_core_dependencies
    install_core_dependencies()

import argparse
import sys

from pimlico.test.pipeline import run_test_suite
from pimlico.utils.logging import get_console_logger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline test suite runner")
    parser.add_argument("suite_file", help="CSV file in which each line contains a path to a pipeline config file "
                                           "(potentially relative to test data dir), then a list of modules to test")
    parser.add_argument("--no-clean", help="Do not clean up the storage directory after running tests. By default, "
                                           "all output from the test pipelines is deleted at the end",
                        action="store_true")
    parser.add_argument("--no-clean-after", "-n",
                        help="Do not clean up the storage directory after running tests, but do empty it before "
                             "tests start. By default, all output from the test pipelines is deleted at the end",
                        action="store_true")
    parser.add_argument("--debug", "-d",
                        help="Execute modules in debug mode, potentially giving more verbose output",
                        action="store_true")
    parser.add_argument("--exit-error", "-x", help="Stop after the first error encountered. By default, the error "
                                                   "will be reporting and the next test will continue. This will "
                                                   "cause the whole suite to be aborted if a test fails",
                        action="store_true")
    opts = parser.parse_args()

    log = get_console_logger("Test")

    with open(opts.suite_file, "r") as f:
        rows = [row.split(",") for row in f.read().splitlines() if not row.startswith("#") and len(row.strip())]
    pipelines_and_modules = [(row[0].strip(), [m.strip() for m in row[1:]]) for row in rows]
    log.info("Running {} test pipelines".format(len(pipelines_and_modules)))

    failed = run_test_suite(pipelines_and_modules, log, no_clean=opts.no_clean, stop_on_error=opts.exit_error,
                            no_clean_after=opts.no_clean_after, debug=opts.debug)
    if failed:
        log.error("Some tests did not complete successfully: {}. See above for details".format(
            ", ".join("{}[{}]".format(pipeline, ",".join(modules)) for (pipeline, modules) in failed)
        ))
    else:
        log.info("All tests completed successfully")
    sys.exit(1 if failed else 0)
