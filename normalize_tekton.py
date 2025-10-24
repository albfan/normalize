#!/usr/bin/env python3
"""
normalize_durations.py

Normalize duration strings in YAML files (e.g. "15m0s" -> "15m", "1h0m0s" -> "1h").

Usage:
  # normalize all duration-like scalars in-place for a file
  ./normalize_durations.py --inplace input.yaml

  # read stdin and write to stdout (no inplace)
  cat input.yaml | ./normalize_durations.py - > out.yaml
"""
import re
import sys
import argparse
from pathlib import Path
import yaml
import json

DURATION_RE = re.compile(r'^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')

def normalize_duration(s: str) -> str:
    m = DURATION_RE.fullmatch(s)
    if not m:
        return s
    h, mm, ss = m.groups()
    parts = []
    if h and int(h) != 0:
        parts.append(f"{int(h)}h")
    if mm and int(mm) != 0:
        parts.append(f"{int(mm)}m")
    if ss and int(ss) != 0:
        parts.append(f"{int(ss)}s")
    # If everything was zero or nothing matched, return "0s" to be explicit
    if not parts:
        return "0s"
    return "".join(parts)


def delete_recursive(obj, path):
    """
    Remove all occurrences of a nested key specified by a dotted path
    (e.g. "metadata.creationTimestamp") from the given object in-place.

    Works with nested dicts and lists. Returns the number of removals performed.

    Examples:
        obj = {
            "metadata": {"creationTimestamp": "x", "other": 1},
            "items": [
                {"metadata": {"creationTimestamp": "y"}},
                {"nested": {"metadata": {"creationTimestamp": "z"}}}
            ]
        }
        delete_recursive(obj, "metadata.creationTimestamp")
        # all three creationTimestamp keys removed
    """
    parts = path.split(",")

    def _remove(o, parts):
        if not parts:
            return 0
        head, *tail = parts
        removed = 0

        if isinstance(o, dict):
            # If the head key exists at this level, try to remove/recurse into it
            if head in o:
                if not tail:
                    # final part: delete the key at this level
                    del o[head]
                    return 1
                else:
                    removed += _remove(o[head], tail)
            # Also continue searching other values for matches deeper in the structure
            for v in list(o.values()):
                removed += _remove(v, parts)
        elif isinstance(o, list):
            for item in o:
                removed += _remove(item, parts)
        # primitives / None -> nothing to do
        return removed

    return _remove(obj, parts)

def walk(obj):
    # Recursively walk the YAML structure and normalize strings.
    if isinstance(obj, dict):
        delete_recursive(obj, "metadata,creationTimestamp")
        delete_recursive(obj, "metadata,generation")
        delete_recursive(obj, "metadata,labels,paas.redhat.com/appcode")
        delete_recursive(obj, "metadata,namespace")
        delete_recursive(obj, "metadata,resourceVersion")
        delete_recursive(obj, "metadata,uid")
        new = {}
        for k, v in obj.items():
            if k == "timeout" and isinstance(v, str):
                new[k] = normalize_duration(v)
            elif k == "kind" and v == "Task":
                pass
            elif k == "type" and v == "string":
                pass
            elif k == "apiVersion" and v == "tekton.dev/v1":
                new[k] = "tekton.dev/v1beta1"
            elif k == "metadata" and v == {}:
                pass
            elif k == "computeResources" and v == {}:
                pass
            elif k == "spec" and v == None:
                pass
            elif k == "name" and v == '':
                pass
            elif k == "value" and isinstance(v, str):
                try:
                    jv = json.loads(v)
                    new[k] = jv
                except Exception as e:
                    new[k] = v
            else:
                new[k] = walk(v)
        return new
    elif isinstance(obj, list):
        return [walk(i) for i in obj]
    else:
        return obj

def process_stream(stream):
    docs = list(yaml.safe_load_all(stream))
    out_docs = [walk(doc) for doc in docs]
    # Dump with safe_dump_all
    return yaml.safe_dump_all(out_docs, default_flow_style=False) #, sort_keys=False

def main():
    p = argparse.ArgumentParser()
    p.add_argument('paths', nargs='*', help='files to process; if none, read stdin')
    p.add_argument('--inplace', action='store_true', help='overwrite files in-place')
    args = p.parse_args()

    if not args.paths:
        out = process_stream(sys.stdin)
        sys.stdout.write(out)
        return

    for path in args.paths:
        path = Path(path)
        if not path.exists():
            print(f"skipping missing file: {path}", file=sys.stderr)
            continue
        text = path.read_text()
        out = process_stream(text)
        if args.inplace:
            # safe write via temp file
            tmp = path.with_suffix(path.suffix + ".normalize_tmp")
            tmp.write_text(out)
            tmp.replace(path)
            print(f"normalized {path}")
        else:
            sys.stdout.write(out)

if __name__ == "__main__":
    main()
