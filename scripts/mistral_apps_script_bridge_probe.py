#!/usr/bin/env python3
import os,json,re,time,urllib.request,urllib.error,hashlib

APP='https://script.google.com/macros/s/AKfycbw7faKzElrmV3GZxbgRxOOfUUwnF3ZmIp_LzNrheSOZI2wHZjadiHbzZuZXxVEkYq8Ggg/exec'
MISTRAL=os.environ.get('MISTRAL_API_KEY','')
GH=os.environ.get('GH_TOKEN','')
REPO=os.environ.get('GITHUB_REPOSITORY','milkivc/atlas-vivo-milk')
ISSUE=os.environ.get('ISSUE_NUMBER','35')

def comment(msg):
 print(msg,flush=True)
 if not (GH and ISSUE): return
 try:
  req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments',data=json.dumps({'body':msg}).encode(),method='POST',headers={'Authorization':'Bearer '+GH,'Content-Type':'application/json','Accept':'application/vnd.github+json'})
  urllib.request.urlopen(req,timeout=30).read()
 except Exception as e: print('COMMENT_FAILED '+type(e).__name__,flush=True)

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'MILK-Mistral-Migration-Probe/1.0','Accept':'text/html,application/json,text/plain,*/*'})
 with urllib.request.urlopen(req,timeout=45) as r:
  body=r.read(2_000_000)
  return {'status':getattr(r,'status',200),'url':r.geturl(),'content_type':r.headers.get('content-type',''),'length':len(body),'sha256':hashlib.sha256(body).hexdigest(),'text':body.decode('utf-8','replace')}

def mreq(url,method='GET',payload=None,retries=5):
 data=None if payload is None else json.dumps(payload).encode(); h={'Authorization':'Bearer '+MISTRAL,'Content-Type':'application/json'}; last=None
 for i in range(retries):
  try:
   req=urllib.request.Request(url,data=data,method=method,headers=h)
   with urllib.request.urlopen(req,timeout=70) as r:return json.loads(r.read().decode())
  except Exception as e:last=e;time.sleep(min(2**i,12))
 raise last

def pick_agent():
 page=mreq('https://api.mistral.ai/v1/agents/pages'); agents=page.get('data',page if isinstance(page,list) else [])
 def score(a):
  s=((a.get('name')or'')+' '+(a.get('description')or'')).lower();return sum(k in s for k in ('migra','preserv','interop','transfer'))
 agents=sorted(agents,key=score,reverse=True)
 return agents[0] if agents else None

def sanitize(text):
 # Only send public Web App response to Mistral; strip very long data/blob URLs.
 text=re.sub(r'data:[^\s"\']{200,}','[DATA_URL_REMOVED]',text)
 return text[:60000]

def main():
 if not MISTRAL: raise RuntimeError('MISTRAL_API_KEY missing')
 comment('MISTRAL_APPS_SCRIPT_BRIDGE_PROBE_STARTED method=GET drive_writes=0')
 res=get(APP)
 comment(f"APPS_SCRIPT_WEBAPP_REACHED status={res['status']} content_type={res['content_type'][:80]} bytes_sampled={res['length']} sha256={res['sha256']}")
 agent=pick_agent()
 if not agent: raise RuntimeError('no Mistral agent available')
 prompt='''És o agente MILK de Migração Preservativa. Analisa APENAS a resposta pública de uma Web App Google Apps Script já existente no Atlas. Não tens segredos e não deves pedir segredos. Determina se a página contém endpoints, parâmetros, funções ou links que permitam INVENTÁRIO/EXPORTAÇÃO em modo apenas-leitura. Não inventes. Não proponhas POST nem escrita no Drive. Responde numa única linha JSON: {"usable_bridge":true|false,"safe_get_urls":[...],"evidence":"..."}. Mantém safe_get_urls apenas no mesmo deployment script.google.com e somente GET.'''
 inputs=prompt+'\n\nURL_FINAL='+res['url']+'\nCONTENT_TYPE='+res['content_type']+'\nBODY:\n'+sanitize(res['text'])
 conv=mreq('https://api.mistral.ai/v1/conversations','POST',{'agent_id':agent['id'],'inputs':inputs})
 text=' '.join(str(o.get('content','')) for o in conv.get('outputs',[]) if isinstance(o,dict))
 m=re.search(r'\{.*\}',text,re.S)
 out={'usable_bridge':False,'safe_get_urls':[],'evidence':'Mistral returned no parseable JSON'}
 if m:
  try: out=json.loads(m.group(0))
  except: pass
 safe=[]
 for u in out.get('safe_get_urls',[]) if isinstance(out,dict) else []:
  if isinstance(u,str) and u.startswith(APP): safe.append(u)
 out['safe_get_urls']=safe[:12]
 comment('MISTRAL_APPS_SCRIPT_ANALYSIS '+json.dumps(out,separators=(',',':'),ensure_ascii=False)[:3500])
 # Probe only agent-approved GET URLs, no mutation.
 for i,u in enumerate(safe[:8],1):
  try:
   r=get(u); snippet=re.sub(r'\s+',' ',r['text'][:500])
   comment(f"APPS_SCRIPT_SAFE_GET_{i} status={r['status']} type={r['content_type'][:60]} bytes={r['length']} sha256={r['sha256']} snippet={snippet[:350]}")
  except Exception as e: comment(f'APPS_SCRIPT_SAFE_GET_{i}_FAILED cause={type(e).__name__}:{str(e)[:250]}')

try:main()
except Exception as e:
 comment('MISTRAL_APPS_SCRIPT_BRIDGE_PROBE_FAILED drive_writes=0 cause='+str(e).replace('\n',' ')[:700]);raise
