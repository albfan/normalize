#!/usr/bin/env python

import sys
from ruamel.yaml import YAML

inp = """\
# example
name:
  # details
  family: Smith   # very common
  given: Alice    # one of the siblings
address:
  #Details on location
  street: Lany Road
  #Portal number
  number: 6
  floor: 1
  side: B
"""

yaml = YAML()
code = yaml.load(inp)
print(type(code))
code['name']['given'] = 'Bob'
code['address']['number'] = 12
del code['address']['side']
path = "address,floor"
parts = path.split(",")
o = code
*init,tail = parts
for i in init:
    o = o[i]
del o[tail]

yaml.dump(code, sys.stdout)
