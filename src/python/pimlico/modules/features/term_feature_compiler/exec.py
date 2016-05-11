# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from collections import Counter

from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def process_document(worker, archive, filename, doc):
    term_keys = worker.info.options["term_keys"]
    output_data_points = []

    for data_point in doc:
        # Look for the special keys we use as terms
        try:
            term = (val for (key, val) in data_point if key in term_keys).next()
        except StopIteration:
            # No term keys found in the data point: skip it
            continue
        # Take all the other keys as feature counts
        if worker.info.options["include_feature_keys"]:
            features = ["%s_%s" % (key, value) for (key, value) in data_point if key not in term_keys]
        else:
            features = [value for (key, value) in data_point if key not in term_keys]
        feature_counts = dict(Counter(features))
        output_data_points.append((term, feature_counts))
    return output_data_points


ModuleExecutor = multiprocessing_executor_factory(process_document)