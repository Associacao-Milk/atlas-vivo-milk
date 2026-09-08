#!/usr/bin/env python3
import os,re,json,hashlib,urllib.request
s=os.environ.get('DRIVE_SOMOSTODOSPOSSIVEIS','')
gh=os.environ.get('GH_TOKEN',''); repo=os.environ.get('GITHUB_REPOSITORY','milkivc/atlas-vivo-milk'); issue=os.environ.get('ISSUE_NUMBER','35')
def typ(t):
 t=t.strip().strip('"\'')
 if not t:return 'empty'
 if t.startswith('{') and t.endswith('}'):
  try:
   d=json.loads(t)
   if d.get('type')=='service_account':return 'service_account_json'
   if d.get('type')=='authorized_user':return 'authorized_user_json'
   if d.get('refresh_token'):return 'oauth_json_with_refresh'
   if 'installed' in d or 'web' in d:return 'oauth_client_json'
   return 'json_object_other'
  except:return 'brace_wrapped_nonjson'
 if t.startswith('4/'):return 'oauth_authorization_code'
 if t.startswith('4%2F'):return 'oauth_authorization_code_urlencoded'
 if t.startswith('1//') or re.match(r'^1/[A-Za-z0-9_-]{15,}$',t):return 'refresh_token'
 if t.startswith('ya29.'):return 'access_token'
 if t.startswith('GOCSPX-'):return 'oauth_client_secret'
 if t.startswith('AIza'):return 'google_api_key'
 if re.fullmatch(r'[0-9]+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com',t):return 'oauth_client_id'
 if re.match(r'^https?://',t):return 'url'
 if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*=',t):return 'key_value_line'
 if re.fullmatch(r'[0-9]+',t):return 'digits_only'
 return 'opaque_other'
lines=[x for x in re.split(r'[\r\n]+',s.strip()) if x.strip()]
parts=[]
for ln in lines[:20]:
 if '=' in ln and re.match(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*=',ln):
  k,v=ln.split('=',1);parts.append('kv:'+re.sub(r'[^A-Za-z0-9_]','',k)[:48]+':'+typ(v))
 else:parts.append(typ(ln))
embedded=[]
for label,pat in [('auth_code',r'4/[A-Za-z0-9._~+/-]{10,}'),('refresh',r'1//[A-Za-z0-9._~-]{10,}'),('access',r'ya29\.[A-Za-z0-9._~-]{10,}'),('client_secret',r'GOCSPX-[A-Za-z0-9_-]{10,}'),('client_id',r'[0-9]+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com')]:
 if re.search(pat,s):embedded.append(label)
shape={'length_bucket':('<100' if len(s)<100 else '100-499' if len(s)<500 else '500-1999' if len(s)<2000 else '>=2000'),'line_count':len(lines),'line_types':parts,'embedded_types':embedded,'has_braces':('{' in s and '}' in s),'has_equals':'=' in s,'has_colon':':' in s,'has_spaces':bool(re.search(r'\s',s)),'fingerprint12':hashlib.sha256(s.encode()).hexdigest()[:12]}
msg='DRIVE_SECRET_SHAPE '+json.dumps(shape,separators=(',',':'));print(msg)
if gh and issue:
 data=json.dumps({'body':msg}).encode();req=urllib.request.Request(f'https://api.github.com/repos/{repo}/issues/{issue}/comments',data=data,method='POST',headers={'Authorization':'Bearer '+gh,'Content-Type':'application/json','Accept':'application/vnd.github+json'});urllib.request.urlopen(req,timeout=30).read()
