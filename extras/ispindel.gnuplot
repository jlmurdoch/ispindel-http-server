set datafile separator whitespace
set xdata time
set timefmt "%Y-%m-%d %H:%M:%S"
plot "ispindel.log" using 1:16 with linesv
