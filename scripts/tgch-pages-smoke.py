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
if not ("The Grateful Catholic Heart" in home and "heartAudioAlerts" in home):
 raise SystemExit("TGCH QA: homepage or audio alert checkbox missing")
if not ("tgch-recorded-player.js" in archive and "tgchRecordedAudio" in archive):
 raise SystemExit("TGCH QA: Heart audio reader missing")
if not ("showNotification" in sw and "notificationclick" in sw):
 raise SystemExit("TGCH QA: Prayer Bell push service worker missing")
if not ("af_heart" in player and "tgch-heart-audio" in player):
 raise SystemExit("TGCH QA: verified Heart player missing")
print("TGCH "+args.target+" smoke PASS "+args.source_sha[:12])
