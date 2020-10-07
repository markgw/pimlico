# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import os

from pimlico.core.config import PipelineConfig


def get_pipeline():
    pipeline_path = os.environ.get("JUPYTER_PIPELINE", None)
    if pipeline_path is None:
        raise EnvironmentError("a currently loaded pipeline was not available. Are you running this code from a "
                               "Jupyter notebook launched by the Pimlico 'jupyter' command?")
    return PipelineConfig.load(filename=pipeline_path)
