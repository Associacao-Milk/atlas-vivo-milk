#!/usr/bin/env python3
import os,re,json,base64,urllib.parse
s=os.environ.get('DRIVE_SOMOSTODOSPOSSIVEIS','').strip().lstrip('\ufeff')
# unwrap code fence and KEY=value wrappers
s=re.sub(r'^```(?:json|text|ini)?\s*','',s,flags=re.I); s=re.sub(r'\s*```$','',s)
m=re.match(r'^[A-Z0-9_]{3,80}\s*=\s*(.+)$',s,re.S)
if m:s=m.group(1).strip()
# JSON string wrapper such as "ya29..." or "{...}"
try:
 d=json.loads(s)
 if isinstance(d,str):s=d.strip()
except Exception:pass
# URL decoding from copied browser/CLI values
try:
 u=urllib.parse.unquote(s)
 if u:s=u
except Exception:pass
# recover embedded complete JSON object
start=s.find('{')
if start>=0:
 try:
  d,end=json.JSONDecoder().raw_decode(s[start:])
  if isinstance(d,dict):
   print(json.dumps(d,separators=(',',':')),end='');raise SystemExit
 except SystemExit:raise
 except Exception:pass
# recover known Google bearer/refresh/auth tokens embedded in explanatory text
patterns=[
 r'(ya29\.[A-Za-z0-9._~+/-]{20,})',
 r'(1//[A-Za-z0-9._~+/-]{20,})',
 r'(1/[A-Za-z0-9_-]{20,})',
 r'(4/[A-Za-z0-9._~+/-]{10,})',
 r'(GOCSPX-[A-Za-z0-9_-]{10,})',
 r'([0-9]+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com)',
 r'(AIza[A-Za-z0-9_-]{20,})']
for p in patterns:
 m=re.search(p,s)
 if m:
  print(m.group(1),end='');raise SystemExit
# base64 wrapper containing one of the above/JSON/rclone config
if len(s)>24 and re.fullmatch(r'[A-Za-z0-9_+/=-]+',s):
 for decoder in (base64.b64decode,base64.urlsafe_b64decode):
  try:
   raw=s.encode()+b'='*((4-len(s)%4)%4); d=decoder(raw).decode('utf-8').strip()
   if d and d!=s:
    print(d,end='');raise SystemExit
  except SystemExit:raise
  except Exception:pass
print(s,end='')
