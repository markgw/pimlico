# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

# Template plotting script that will be copied into the output dir so that it's easy to customize the plot afterwards
"""
This is a basic template for plotting a bar chart of the data in data.csv. It's been output by Pimlico's
bar chart plotting module and you should find that its output is available already in plot.pdf. However, you
can now customize your plot if you like, by modifying this file and running:
    python plot.py

"""
from builtins import zip
from backports import csv

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
matplotlib.rc('font', family="Gentium", size=8)
import matplotlib.pyplot as plt
import numpy
import io

bar_width = 0.5

# Read in the input data
with io.open("data.csv", "r") as f:
    csv_reader = csv.reader(f)
    # Should be two values in each row
    labels, xs, ys, colours = list(zip(*csv_reader))

xs = numpy.array([float(v) for v in xs])
ys = numpy.array([float(v) for v in ys])

# Plot the data
fig = plt.figure()
ax = fig.add_subplot(111)

plt.scatter(xs, ys, s=1)

for x, y, label, c in zip(xs, ys, labels, colours):
    plt.text(x, y, label, horizontalalignment="center", color=c)

plt.title("<TITLE>")
plt.savefig("plot.pdf", transparent=True)
