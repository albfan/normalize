# normalize

## Description

Rework your value representation, order and indent on your data

## About

Manipulating your data (text, raw, source code), is usually interesting to normalize it.

Double space, wrapping, max line length, indentation style (tab/spaces), format ({ and newlines, spaces on params). 
All that prepare your info to be safely manipulated. Diffting, pushing upstream.

Here, some formal changes that do not represent a change on information will try to be "normalized":

- double/single quotes 
- default values
- timestamp values

and having in mind a final step: If normalized data expose a needed change, can we apply to the "unnormalized"original data?

## Examples:

- yaml:

original:
```
- b: 1
- a: 2
```

changed:
```
- b: 1
- a: 2
```

original and changed represent same info, if we want to change `a` to `3` can we still apply on original yaml

