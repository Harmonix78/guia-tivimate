"""Builds guide.xml.gz for TiviMate: only the channels in channels.json, each renamed to the exact name it has in the
playlist, so TiviMate matches them by name with no manual work.

channels.json: {"playlist channel name": ["epgshare01 file", "epgshare01 channel id"], ...}
"""
import datetime as dt, gzip, json, sys, urllib.request, xml.etree.ElementTree as ET
from collections import defaultdict

BASE = "https://epgshare01.online/epgshare01/epg_ripper_{}.xml.gz"
# Only what TiviMate will show: from 6 hours ago to 5 days ahead (the sources carry a day or two of the past).
NOW = dt.datetime.now(dt.timezone.utc)
FROM, UNTIL = NOW - dt.timedelta(hours=6), NOW + dt.timedelta(days=5)
def keep(el):
    try:
        return dt.datetime.strptime(el.get("stop"), "%Y%m%d%H%M%S %z") >= FROM and \
            dt.datetime.strptime(el.get("start"), "%Y%m%d%H%M%S %z") <= UNTIL
    except (TypeError, ValueError):
        return True
channels = json.load(open("channels.json", encoding="utf-8"))
by_source = defaultdict(lambda: defaultdict(list))          # file -> source id -> [playlist names]
for name, (src, cid) in channels.items():
    by_source[src][cid].append(name)

out_channels, out_programmes, found = [], [], set()
for src, ids in sorted(by_source.items()):
    req = urllib.request.Request(BASE.format(src), headers={"User-Agent": "guia-tivimate/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, gzip.GzipFile(fileobj=r) as g:
            n = 0
            for _, el in ET.iterparse(g, events=("end",)):
                cid = el.get("id") if el.tag == "channel" else el.get("channel") if el.tag == "programme" else None
                if cid in ids:
                    for name in ids[cid]:
                        if el.tag == "channel":
                            ch = ET.Element("channel", id=name)
                            ET.SubElement(ch, "display-name").text = name
                            icon = el.find("icon")
                            if icon is not None: ch.append(icon)
                            out_channels.append(ch)
                            found.add(name)
                        elif keep(el):
                            p = ET.Element("programme", dict(el.attrib, channel=name))
                            p.extend(list(el))
                            out_programmes.append(p)
                            n += 1
                if el.tag in ("channel", "programme"): el.clear()
            print(f"{src}: {n} programas", flush=True)
    except Exception as e:                    # one source down must not empty the whole guide
        print(f"{src}: ERROR {e}", file=sys.stderr)

if len(found) < len(channels) // 2:
    sys.exit(f"Solo {len(found)} de {len(channels)} canales: no se publica una guía rota")
root = ET.Element("tv", {"generator-info-name": "guia-tivimate"})
root.extend(out_channels)
root.extend(out_programmes)
with gzip.open("guide.xml.gz", "wb", compresslevel=9) as f:
    ET.ElementTree(root).write(f, encoding="utf-8", xml_declaration=True)
missing = sorted(set(channels) - found)
print(f"{len(found)} canales con guía, {len(out_programmes)} programas; sin datos hoy: {len(missing)}")
for m in missing: print("  -", m)
