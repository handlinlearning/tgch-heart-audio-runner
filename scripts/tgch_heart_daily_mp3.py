#!/usr/bin/env python3
"""Immutable TGCH af_heart MP3: original must pass SHA-256 before synthesizing."""
import argparse, hashlib, json, os, re, subprocess, tempfile, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from zoneinfo import ZoneInfo

BASE = "https://qgxoombbfmimpbcollhi.supabase.co/functions/v1/"
AUD = "tgch-heart-audio-upload"

def get(url, auth=None):
    headers = {"Accept": "application/json"}
    if auth: headers["Authorization"] = auth
    with urlopen(Request(url, headers=headers), timeout=50) as r:
        return json.load(r)

def words(md):
    # Remove display-only markup for speech, never modify archived text.
    md = re.sub(r'<Entity\b[^>]*\bvalue="([^"]+)"[^>]*/>', r'\1', md)
    md = re.sub(r'</?text\b[^>]*>', '', md, flags=re.I)
    md = re.sub(r'(?m)^\s*#{1,6}\s+', '', md)
    md = re.sub(r'(?m)^\s*>\s?', '', md)
    md = re.sub(r'(?m)^\s*(?:---+|___+|\*\*\*+)\s*$', '', md)
    md = re.sub(r'(?m)^\s*[-+*]\s+(?=\S)', '', md)
    md = re.sub(r'(?m)^\s*\d+[.)]\s+(?=\S)', '', md)
    md = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', md)
    md = md.replace('**', '').replace('`', '')
    md = re.sub(r'(?<!\S)\*([^*\n]+)\*(?!\S)', r'\1', md)
    return re.sub(r'\n{3,}', '\n\n', md).strip()

def oidc():
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not token: raise RuntimeError("Must run from GitHub Actions with id-token:write")
    u = url + ("&" if "?" in url else "?") + "audience=" + quote(AUD, safe="")
    return get(u, "Bearer "+token)["value"]

def render(text, output):
    from kokoro import KPipeline
    import numpy as np
    import soundfile as sf
    generator = KPipeline(lang_code="a", device="cpu")
    parts = []
    count = 0
    for _,_,clip in generator(text,voice="af_heart",speed=0.94,split_pattern=r'\n+'):
        if clip is not None and len(clip):
            parts.append(np.asarray(clip,dtype=np.float32))
            parts.append(np.zeros(5760,dtype=np.float32))
            count += 1
    if not count: raise RuntimeError("No speech generated; refusing publication")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td)/"heart.wav"
        sf.write(wav,np.concatenate(parts),24000)
        subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
           "-y","-i",str(wav),"-codec:a","libmp3lame","-b:a","96k",
           "-ar","24000","-ac","1",str(output)],check=True)
    if not 10000 < output.stat().st_size < 30000000:
        raise RuntimeError("Unsafe MP3 size")
    print("Original narration segments generated:",count)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",default=datetime.now(ZoneInfo("America/Chicago")).date().isoformat())
    date=parser.parse_args().date
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',date):
        raise RuntimeError("Invalid date")
    try: src=get(BASE+"tgch-devotionals?date="+quote(date))
    except HTTPError as e:
        if e.code==404:
            print("No verified original for",date,"— safely skipped");return
        raise
    md=src.get("markdown")
    sha=src.get("sha256")
    if src.get("date")!=date or not isinstance(md,str) or not re.fullmatch(r'[0-9a-f]{64}',sha or ''):
        raise RuntimeError("Invalid published original response")
    if hashlib.sha256(md.encode("utf8")).hexdigest()!=sha:
        raise RuntimeError("Original SHA-256 mismatch; no recording")
    state=get(BASE+"tgch-heart-audio?date="+quote(date))
    if state.get("available"):
        if state.get("source_sha256")==sha and state.get("voice")=="af_heart":
            print("Existing verified recording; nothing to regenerate");return
        raise RuntimeError("Existing recording conflicts with source")
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/"heart.mp3"
        render(words(md),file)
        audio=file.read_bytes()
        audio_sha=hashlib.sha256(audio).hexdigest()
        request=Request(BASE+"tgch-heart-audio?date="+quote(date),data=audio,method="POST",headers={
            "Authorization":"Bearer "+oidc(),
            "Content-Type":"audio/mpeg",
            "X-TGCH-Source-SHA256":sha,
            "X-TGCH-Audio-SHA256":audio_sha})
        with urlopen(request,timeout=120) as r: receipt=json.load(r)
        if not receipt.get("published"):raise RuntimeError("Unconfirmed audio publication")
        check=get(BASE+"tgch-heart-audio?date="+quote(date))
        if not check.get("available") or check.get("audio_sha256")!=audio_sha or check.get("source_sha256")!=sha:
            raise RuntimeError("Post-upload integrity check failed")
        print("Heart MP3 published",date,len(audio),"bytes, source matched")

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("TGCH Heart failed safely:",e,file=sys.stderr)
        sys.exit(1)
