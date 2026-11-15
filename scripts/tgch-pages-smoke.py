#!/usr/bin/env python3
"""Read-only smoke checks on Cloudflare preview/production. Never deploy or write content."""
import argparse, time, urllib.request, urllib.parse, sys
parser=argparse.ArgumentParser()
parser.add_argument("--url",required=True)
parser.add_argument("--source-sha",required=True)
parser.add_argument("--target",choices=["preview","production"],required=True)
args=parser.parse_args()
url=args.url.strip().rstrip("/")
u=urllib.parse.urlparse(url)
if u.scheme!="https" or not u.hostname:
 raise SystemExit("TGCH QA: HTTPS URL required")
if args.target=="preview" and not u.hostname.endswith(".pages.dev"):
 raise SystemExit("TGCH QA: not a Cloudflare Pages preview")
if args.target=="production" and u.hostname!="thegratefulcatholicheart.com":
 raise SystemExit("TGCH QA: unexpected production domain")
if not (len(args.source_sha)==40 and all(c in "0123456789abcdef" for c in args.source_sha)):
 raise SystemExit("TGCH QA: invalid source SHA")
def get(path):
 req=urllib.request.Request(url+path,headers={"User-Agent":"TGCH-Release-QA/1.0","Cache-Control":"no-cache"})
 with urllib.request.urlopen(req,timeout=20) as response:
  if response.status!=200: raise RuntimeError("HTTP "+str(response.status))
  return response.read(1200000).decode("utf-8","replace")
ok=False
for attempt in range(12):
 try:
  marker=get("/tgch-release-sha.txt").strip()
  if marker==args.source_sha:
   ok=True
   break
 except Exception as ex:
  print("TGCH marker retry",attempt+1,type(ex).__name__)
 time.sleep(5)
if not ok: raise SystemExit("TGCH QA: deployment marker failed: refusing release confirmation")
home=get("/")
archive=get("/a-little-something-extra.html")
sw=get("/tgch-sw.js")
player=get("/tgch-recorded-player.js")
extra_delivery=get("/tgch-extra-delivery.js")
reader=get("/a-little-something-extra.js")
sunday=get("/tgch-sunday-companion.js")
if not ("The Grateful Catholic Heart" in home and "heartAudioAlerts" in home):
 raise SystemExit("TGCH QA: homepage or audio alert checkbox missing")
if not ("tgch-recorded-player.js" in archive and "tgchRecordedAudio" in archive):
 raise SystemExit("TGCH QA: Heart audio reader missing")
if not ('id="extraPushEnable"' in archive and 'id="extraShare"' in archive and
        "tgch-extra-delivery.js" in archive):
 raise SystemExit("TGCH QA: separate daily phone subscribe/share controls missing")
if not ("tgch-extra-device" in extra_delivery and "tgch:original:verified" in extra_delivery):
 raise SystemExit("TGCH QA: daily phone subscription and verified sharing code missing")
if not ('id="tgchSundayCompanion"' in archive and "tgch-sunday-companion.js?v=2" in archive and
        'id="tgchSundayCorrection"' not in archive and "tgch-extra-delivery.js?v=2" in archive):
 raise SystemExit("TGCH QA: Sunday readings-only page must contain no correction notices")
if not ("bible.usccb.org" in sunday and "Matthew 25:14" in sunday and
        "tgch:sunday:selected" in sunday and "Luke 21:5" not in sunday and "correction" not in sunday):
 raise SystemExit("TGCH QA: Sunday must use official reading references, not correction displays")
if not ("if(showSundayOnly(date))return;" in reader and "originalArea.hidden=true" in reader and
        "tgch:sunday:selected" in reader):
 raise SystemExit("TGCH QA: generated Sunday original must be hidden from public site")
if not ('sundaySelected?"#tgchSundayCompanion":"#listen"' in extra_delivery):
 raise SystemExit("TGCH QA: Sunday sharing must link to the readings, not original audio")
if not ("showNotification" in sw and "notificationclick" in sw):
 raise SystemExit("TGCH QA: Prayer Bell push service worker missing")
if not ("af_heart" in player and "tgch-heart-audio" in player):
 raise SystemExit("TGCH QA: verified Heart player missing")
print("TGCH "+args.target+" smoke PASS "+args.source_sha[:12])
