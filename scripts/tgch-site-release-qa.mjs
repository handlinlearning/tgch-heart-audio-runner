#!/usr/bin/env node
// TGCH public-runner local site release gate. Never rewrites original devotional data.
import {readFileSync, existsSync, readdirSync, lstatSync} from "node:fs";
import {join, resolve, relative} from "node:path";
import {createHash} from "node:crypto";
import {execFileSync} from "node:child_process";

const root=resolve(process.argv[2]||"tgch-source/site");
const required=[
 "index.html","styles.css","app.js","tgch-sw.js",
 "tgch-config.js","tgch-formation-2026-2027.json",
 "a-little-something-extra.html","a-little-something-extra.js",
 "tgch-recorded-player.js","manifest.webmanifest",
 "assets/tgch-logo.png","assets/tgch-v4/crest-official.webp",
 "assets/tgch-v4/hero-reference-rebuilt.webp"
];
// The approved original formation and exact-original renderer/service worker are locked.
const locked={
 "tgch-formation-2026-2027.json":"a0da0e7c622ef1e6083a012dae4c5bff340686b9",
 "a-little-something-extra.js":"218a57725b244078d513b43247d201ea5489a1c6",
 "tgch-sw.js":"976cb608a0fbd01b9c5be7db8d09e981c2d57847"
};
const assert=(ok,msg)=>{if(!ok)throw new Error("TGCH QA: "+msg);};
const blobSha=b=>createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");
for(const file of required){
 const path=join(root,file);
 assert(existsSync(path)&&!lstatSync(path).isSymbolicLink()&&lstatSync(path).isFile(),"missing/unsafe "+file);
 assert(readFileSync(path).length>200,"empty "+file);
}
for(const [name,sha] of Object.entries(locked)){
 assert(blobSha(readFileSync(join(root,name)))===sha,"approved content changed: "+name);
}
const index=readFileSync(join(root,"index.html"),"utf8");
const extra=readFileSync(join(root,"a-little-something-extra.html"),"utf8");
const app=readFileSync(join(root,"app.js"),"utf8");
assert(index.includes('id="bellDialog"')&&index.includes('id="heartAudioAlerts"'),"Prayer Bell / optional audio settings");
assert(index.includes("One Heart. One Prayer. One Day at a Time."),"approved TGCH identity");
assert(extra.includes("tgch-recorded-player.js")&&extra.includes('id="tgchRecordedAudio"'),"Heart player missing");
assert(app.includes("register-tgch-device")&&app.includes("audio_notifications_enabled"),"notification opt-in missing");
const cfg=readFileSync(join(root,"tgch-config.js"),"utf8");
assert(!/SUPABASE_SERVICE_ROLE_KEY|CLOUDFLARE_API_TOKEN|TGCH_SOURCE_READ_TOKEN/.test(cfg),"secret-like config reference");
function checkTree(folder){
 for(const entry of readdirSync(folder,{withFileTypes:true})){
  const target=join(folder,entry.name);
  assert(!entry.isSymbolicLink(),"symlink "+relative(root,target));
  if(entry.isDirectory())checkTree(target);
  else if(entry.name.endsWith(".js")){
    execFileSync("node",["--check",target],{stdio:"pipe"});
  }
 }
}
checkTree(root);
JSON.parse(readFileSync(join(root,"manifest.webmanifest"),"utf8"));
JSON.parse(readFileSync(join(root,"tgch-formation-2026-2027.json"),"utf8"));
const total=readdirSync(root).length;
assert(total>=15,"site incomplete");
console.log("TGCH verified: complete site, approved formation, original reader, service worker, Prayer Bell, Heart player and JS");
