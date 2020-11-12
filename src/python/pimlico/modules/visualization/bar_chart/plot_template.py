# Template plotting script that will be copied into the output dir so that it's easy to customize the plot afterwards
"""
This is a basic template for plotting a bar chart of the data in data.csv. It's been output by Pimlico's
bar chart plotting module and you should find that its output is available already in plot.pdf. However, you
can now customize your plot if you like, by modifying this file and running:
    python plot.py

"""
from builtins import zip
from builtins import range

import matplotlib
import csv
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt

bar_width = 0.5
COLOURS = ['g', 'b', 'y', 'm', 'c', '#B1C7CA', '#90F0A0']

# Read in the input data
with open("data.csv", "r") as f:
    csv_reader = csv.reader(f)
    labels, values = list(zip(*csv_reader))

values = [float(v) for v in values]
bar_positions = [float(i) - 0.5*bar_width for i in range(len(values))]

# Plot the data
fig = plt.figure()
# Change y-range
#plt.ylim(0, 55)
ax = fig.add_subplot(111)

bars = ax.bar(bar_positions, values, bar_width)
ax.tick_params(
    axis='x',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom='off',      # ticks along the bottom edge are off
    top='off',         # ticks along the top edge are off
    labelbottom='off'
)
for b, bar in enumerate(bars):
    bar.set_color(COLOURS[b % len(COLOURS)])
    bar.set_label(labels[b])

handles, labels = ax.get_legend_handles_labels()
lgd = ax.legend(handles, labels, loc=8, bbox_to_anchor=(0.5, -0.2), ncol=3)

plt.savefig("plot.pdf", bbox_extra_artists=(lgd,), bbox_inches='tight', transparent=True)
