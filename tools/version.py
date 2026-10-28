"""Start the next version of a cut list: copies the latest one to cutlist_v<N+1>.json.

Usage: ./bts version <project>
Updates "(vN)" in the title and prints the new file's path; edit that file, never
an older version.
"""
import json
import os
import re
import sys

from common import project_dir

proj = project_dir(sys.argv[1])
edl = os.path.join(proj, "edl")
versions = sorted(int(m.group(1)) for f in os.listdir(edl) if (m := re.fullmatch(r"cutlist_v(\d+)\.json", f)))
if not versions:
    sys.exit("No cut list yet: write edl/cutlist_v1.json first")
n = versions[-1]
cl = json.load(open(os.path.join(edl, f"cutlist_v{n}.json")))
cl["title"] = re.sub(r"\(v\d+\)", f"(v{n + 1})", cl.get("title", ""))
dst = os.path.join(edl, f"cutlist_v{n + 1}.json")
json.dump(cl, open(dst, "w"), ensure_ascii=False, indent=2)
print(f"v{n} -> {dst}")
