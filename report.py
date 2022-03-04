import texttable
from texttable import Texttable
import json 
import sys

def part1():
  table = Texttable(max_width=0)
  table.set_deco(Texttable.HEADER)
  rows = []
  first_key = next(iter(data))
  columns = ['webpage']
  columns.extend(list(data[first_key].keys()))
  for webpage in data:
    row = [webpage]
    for info in data[webpage]:
      row.append(data[webpage][info])
    rows.append(row)
  # table.set_cols_align(["l"]*len(columns))
  # table.set_cols_valign(["m"]*len(columns)) this is just styling dont need this
  rows.insert(0, columns)
  table.add_rows(rows)
  print(table.draw())

user_in = sys.argv[1]
user_out = sys.argv[2]
f = open(user_in)
data = json.load(f)
f.close()
part1() #need to somehow turn the table printed into a txt file