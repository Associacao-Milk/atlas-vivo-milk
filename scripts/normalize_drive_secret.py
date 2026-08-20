#!/usr/bin/env python3
import os,re,json,base64,urllib.parse,urllib.request,tempfile,subprocess,pathlib,datetime
s=os.environ.get('DRIVE_SOMOSTODOSPOSSIVEIS','').strip().lstrip('\ufeff')
s=re.sub(r'^```(?:json|text|ini)?\s*','',s,flags=re.I); s=re.sub(r'\s*```$','',s)
m=re.match(r'^[A-Z0-9_]{3,80}\s*=\s*(.+)$',s,re.S)
if m:s=m.group(1).strip()
try:
 d=json.loads(s)
 if isinstance(d,str):s=d.strip()
except Exception:pass
try:
 u=urllib.parse.unquote(s)
 if u:s=u
except Exception:pass
start=s.find('{')
if start>=0:
 try:
  d,end=json.JSONDecoder().raw_decode(s[start:])
  if isinstance(d,dict):
   print(json.dumps(d,separators=(',',':')),end='');raise SystemExit
 except SystemExit:raise
 except Exception:pass
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
if len(s)>24 and re.fullmatch(r'[A-Za-z0-9_+/=-]+',s):
 for decoder in (base64.b64decode,base64.urlsafe_b64decode):
  try:
   raw=s.encode()+b'='*((4-len(s)%4)%4); d=decoder(raw).decode('utf-8').strip()
   if d and d!=s:
    print(d,end='');raise SystemExit
  except SystemExit:raise
  except Exception:pass
# Capability probe 1: already-valid rclone config even if formatting escaped classifier regex.
try:
 p=pathlib.Path(tempfile.mkstemp(prefix='milk-rclone-',suffix='.conf')[1]);p.write_text(s,encoding='utf-8');os.chmod(p,0o600)
 q=subprocess.run(['rclone','--config',str(p),'listremotes'],text=True,capture_output=True,timeout=20)
 if q.returncode==0:
  rem=[x.strip() for x in q.stdout.splitlines() if x.strip()]
  for r in rem:
   z=subprocess.run(['rclone','--config',str(p),'config','show',r.rstrip(':')],text=True,capture_output=True,timeout=20)
   if z.returncode==0 and re.search(r'^\s*type\s*=\s*drive\s*$',z.stdout,re.M):
    print(s,end='');raise SystemExit
except SystemExit:raise
except Exception:pass
# Capability probe 2: opaque Bearer token. No response content is printed.
try:
 req=urllib.request.Request('https://www.googleapis.com/drive/v3/about?fields=user',headers={'Authorization':'Bearer '+s})
 with urllib.request.urlopen(req,timeout=20) as r:
  if 200<=r.status<300:
   expiry=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=45)).isoformat().replace('+00:00','Z')
   tok=json.dumps({'access_token':s,'token_type':'Bearer','refresh_token':'','expiry':expiry},separators=(',',':'))
   cfg='[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+tok+'\n'
   print(cfg,end='');raise SystemExit
except SystemExit:raise
except Exception:pass
print(s,end='')
