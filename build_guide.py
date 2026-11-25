"""Builds guide.xml.gz for TiviMate: only the channels in channels.json, each renamed to the exact name it has in the
playlist, so TiviMate matches them by name with no manual work.

channels.json: {"playlist channel name": ["epgshare01 file", "epgshare01 channel id"], ...}; the file can also be
"IPTVORG", with the xmltv_id of an entry in iptvorg.channels.xml (iptv-org/epg's grabber, run before this). Two more
items, ["file", "id", "fallback file", "fallback id"], fill the hours the first source doesn't cover (tvpassport's local
stations start at midnight Eastern of the day of the run, so a run in the evening leaves the rest of that night empty).
"""
import datetime as dt, gzip, json, sys, urllib.request, xml.etree.ElementTree as ET
from collections import defaultdict

BASE = "https://epgshare01.online/epgshare01/epg_ripper_{}.xml.gz"
# Sources that aren't epgshare01 files: guides made by an earlier step of the workflow (iptvorg.channels.xml).
LOCAL = {"IPTVORG": "iptvorg.xml"}
# Only what TiviMate will show: from 6 hours ago to 48 hours ahead (the sources carry a day or two of the past).
NOW = dt.datetime.now(dt.timezone.utc)
FROM, UNTIL = NOW - dt.timedelta(hours=6), NOW + dt.timedelta(hours=48)
def keep(el):
    try:
        return dt.datetime.strptime(el.get("stop"), "%Y%m%d%H%M%S %z") >= FROM and \
            dt.datetime.strptime(el.get("start"), "%Y%m%d%H%M%S %z") <= UNTIL
    except (TypeError, ValueError):
        return True
channels = json.load(open("channels.json", encoding="utf-8"))
by_source = defaultdict(lambda: defaultdict(list))          # file -> source id -> [playlist names]
FALLBACK = "\x00fallback"     # the same playlist name, from its fallback source
for name, v in channels.items():
    by_source[v[0]][v[1]].append(name)
    if len(v) == 4:
        by_source[v[2]][v[3]].append(FALLBACK + name)

out_channels, out_programmes, found = {}, [], set()
fallback_programmes = defaultdict(list)
per_name = defaultdict(int)
for src, ids in sorted(by_source.items()):
    try:
        if src in LOCAL:   # a guide made earlier in this run (iptv-org's grabber); missing = that step failed
            stream = open(LOCAL[src], "rb")
        else:
            req = urllib.request.Request(BASE.format(src), headers={"User-Agent": "guia-tivimate/1.0"})
            stream = gzip.GzipFile(fileobj=urllib.request.urlopen(req, timeout=300))
        with stream as g:
            n = 0
            for _, el in ET.iterparse(g, events=("end",)):
                cid = el.get("id") if el.tag == "channel" else el.get("channel") if el.tag == "programme" else None
                if cid in ids:
                    for name in ids[cid]:
                        if name.startswith(FALLBACK):
                            if el.tag == "programme" and keep(el):
                                p = ET.Element("programme", dict(el.attrib, channel=name[len(FALLBACK):]))
                                p.extend(list(el))
                                fallback_programmes[name[len(FALLBACK):]].append(p)
                            continue
                        if el.tag == "channel":
                            ch = ET.Element("channel", id=name)
                            ET.SubElement(ch, "display-name").text = name
                            icon = el.find("icon")
                            if icon is not None: ch.append(icon)
                            out_channels[name] = ch
                        elif keep(el):
                            p = ET.Element("programme", dict(el.attrib, channel=name))
                            p.extend(list(el))
                            out_programmes.append(p)
                            per_name[name] += 1
                            found.add(name)
                            n += 1
                if el.tag in ("channel", "programme"): el.clear()
            print(f"{src}: {n} programas", flush=True)
    except Exception as e:                    # one source down must not empty the whole guide
        print(f"{src}: ERROR {e}", file=sys.stderr)

# Fallback programmes only where the channel's own source has nothing (before its first or after its last programme).
def when(p, attr): return dt.datetime.strptime(p.get(attr), "%Y%m%d%H%M%S %z")
own = defaultdict(list)
for p in out_programmes: own[p.get("channel")].append(p)
filled = 0
for name, progs in fallback_programmes.items():
    first = min((when(p, "start") for p in own[name]), default=None)
    last = max((when(p, "stop") for p in own[name]), default=None)
    for p in progs:
        try:
            if first is not None and when(p, "stop") > first and when(p, "start") < last: continue
        except (TypeError, ValueError):
            continue
        out_programmes.append(p); per_name[name] += 1; found.add(name); filled += 1
    if name not in out_channels:
        ch = ET.Element("channel", id=name); ET.SubElement(ch, "display-name").text = name
        out_channels[name] = ch
if fallback_programmes: print(f"respaldo: {filled} programas en {len(fallback_programmes)} canales")

if len(found) < len(channels) // 2:
    sys.exit(f"Solo {len(found)} de {len(channels)} canales: no se publica una guía rota")
root = ET.Element("tv", {"generator-info-name": "guia-tivimate"})
root.extend(ch for name, ch in out_channels.items() if per_name[name])
root.extend(out_programmes)
with gzip.open("guide.xml.gz", "wb", compresslevel=9) as f:
    ET.ElementTree(root).write(f, encoding="utf-8", xml_declaration=True)
missing = sorted(set(channels) - found)
print(f"{len(found)} canales con guía, {len(out_programmes)} programas; sin programas hoy: {len(missing)}")
for m in missing: print("  -", m)
