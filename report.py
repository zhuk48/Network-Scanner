import csv
import texttable
from texttable import Texttable
import json 
import sys

def part1():
  table = Texttable(max_width=0)
  table.set_deco(Texttable.HEADER)
  long_columns = ['ipv4_addresses', 'ipv6_addresses', 'rdns_names','rtt_range', 'tls_versions']
  rows = []
  first_key = next(iter(data))
  columns = ['webpage']
  columns.extend(list(data[first_key].keys()))
  for webpage in data:
    row = [webpage]
    for info in data[webpage]:
      if info in long_columns and data[webpage][info] is not None:
        s = '\n'.join(str(e) for e in data[webpage][info])
        row.append(s)
      elif info == 'geo_locations':
        csv_locations = data[webpage][info][0].split(', ')
        dest = []
        for i in range(0, len(csv_locations) - 2, 3):
          s = ' '.join(csv_locations[i:i+3])
          dest.append(s)
        fin = '\n'.join(str(x) for x in dest)
        row.append(fin)
      else:
        row.append(data[webpage][info])
    rows.append(row)
  table.set_cols_align(['l']*13)
  table.set_cols_width((13, 55, 10, 15, 10,20, 20, 10, 5, 10,10, 10, 10))
  # table.set_cols_valign(["m"]*len(columns))
  rows.insert(0, columns)
  table.add_rows(rows)
  pretty_table = table.draw()
  with open('output.txt', 'w', encoding="utf-8") as f:
    f.write(pretty_table)
  # print(pretty_table)

user_in = sys.argv[1]
user_out = sys.argv[2]
f = open(user_in)
data = json.load(f)
f.close()
part1() #need to somehow turn the table printed into a txt file