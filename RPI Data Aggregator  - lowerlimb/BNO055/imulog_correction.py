import csv
import sys


def correct_imu(filename):


  # Open csv file based on timestamp suffix
  with open(filename, 'r') as f:
    reader = csv.reader(f)
    acc_csv = list(reader)

  # Convert csv to a list of floats
  acc_list = []
  acc_timelapse = []
  for k in range(3, len(acc_csv)):
    acc_list.append(float(acc_csv[k-1][0]))
    acc_timelapse.append(float(acc_csv[k][0]) - float(acc_csv[k-1][0]))
    if k == len(acc_csv)-1:
      acc_list.append(float(acc_csv[k][0]))

  # Identify highest peak and adjust intervals
  peak = max(acc_timelapse)
  peak_idx = acc_timelapse.index(max(acc_timelapse))

  if peak > 3*sum(acc_timelapse[:peak_idx])/len(acc_timelapse[:peak_idx]):
    acc_list[peak_idx + 1] = acc_list[peak_idx-1] + sum(acc_timelapse[:peak_idx-1])/len(acc_timelapse[:peak_idx-1])
    for k in range(peak_idx + 2, len(acc_list)):
      acc_list[k] = acc_list[k-1] + acc_timelapse[k-1]

  # Convert back to string and write to csv
  for k in range(2, len(acc_csv)):
    acc_csv[k][0] = str(acc_list[k-2])

  with open(filename, 'w', newline='') as f:
    writer = csv.writer(f, dialect='excel')
    writer.writerows(acc_csv)


if __name__ == '__main__':

  imus = ['Acc_', 'Gyro_']
  for suffix in imus:
    filename = suffix + sys.argv[1] + '.csv'
    correct_imu(filename)