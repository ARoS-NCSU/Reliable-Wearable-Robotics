import csv
import sys

suffix = sys.argv[1]
filename = 'pts_' + suffix + '.dat'

# Open csv file based on timestamp suffix
with open(filename, 'r') as f:
  reader = csv.reader(f)
  camtime_csv = list(reader)

# Convert csv to a list of floats
camtime_list = []
for k in range(1, len(camtime_csv)):
  camtime_list.append([float(camtime_csv[k][0]), float(camtime_csv[k][1])])

# Work on the list and correct gaps
standard_gap = (camtime_list[2][0]-camtime_list[1][0])/1e3

for k in range(1, len(camtime_list)):

  system_timegap = camtime_list[k][1]-camtime_list[k-1][1]
  time_elapsed = (camtime_list[k][0]-camtime_list[k-1][0])/1e3
  if system_timegap < 0.9*standard_gap or system_timegap > 1.1*standard_gap:
      camtime_list[k][1] = camtime_list[k-1][1] + time_elapsed

# Convert back to string and write to csv
for k in range(0, len(camtime_csv)-1):
  camtime_csv[k+1] = [str(camtime_list[k][0]), str(camtime_list[k][1])]

with open(filename, 'w') as f:
  writer = csv.writer(f, dialect='excel')
  writer.writerows(camtime_csv)