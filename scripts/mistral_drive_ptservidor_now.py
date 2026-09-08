#!/usr/bin/env python3
import os, json, base64, re, subprocess, pathlib, urllib.request, time, hashlib, datetime

RUNNER=pathlib.Path(os.environ.get('RUNNER_TEMP','/tmp'))
MISTRAL=os.environ.get('MISTRAL_API_KEY',''); DRIVE_SECRET=os.environ.get('DRIVE_SOMOSTODOSPOSSIVEIS','')
FTPS_PASSWORD=os.environ.get('PTSERVIDOR_FTPS_PASSWORD',''); NEXTCLOUD=os.environ.get('NEXTCLOUD_KEY','')
GH_TOKEN=os.environ.get('GH_TOKEN',''); REPO=os.environ.get('GITHUB_REPOSITORY','milkivc/atlas-vivo-milk'); ISSUE=os.environ.get('ISSUE_NUMBER','35')
FTPS_HOST='troi.ptservidor.net'; FTPS_PORT='21'; FTPS_USER='migration@associacaomilk.pt'

def comment(msg):
    print(msg,flush=True)
    if not(GH_TOKEN and ISSUE): return
    try:
        req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments',data=json.dumps({'body':msg}).encode(),method='POST',headers={'Authorization':'Bearer '+GH_TOKEN,'Content-Type':'application/json','Accept':'application/vnd.github+json'})
        urllib.request.urlopen(req,timeout=30).read()
    except Exception as e: print('COMMENT_FAILED '+type(e).__name__,flush=True)

def run(args,check=True,capture=False):
    p=subprocess.run(args,check=False,text=True,capture_output=capture)
    if check and p.returncode:
        detail=(p.stderr or p.stdout or '')[-800:].replace('\n',' '); raise RuntimeError(f'command_failed rc={p.returncode} detail={detail}')
    return p

def classify_once(t):
    t=t.strip()
    try:
        d=json.loads(t)
        if isinstance(d,dict):
            if d.get('type')=='service_account' and d.get('private_key') and d.get('client_email'): return 'service_account_json'
            if d.get('type')=='authorized_user' and all(d.get(k) for k in ('client_id','client_secret','refresh_token')): return 'authorized_user_json'
            if d.get('refresh_token') and d.get('access_token'): return 'oauth_token_json'
            if d.get('refresh_token'): return 'oauth_refresh_json'
            if 'installed' in d or 'web' in d: return 'oauth_client_json'
    except Exception: pass
    if re.search(r'^\s*\[[^]]+\]\s*$',t,re.M) and re.search(r'^\s*type\s*=\s*drive\s*$',t,re.M): return 'rclone_config'
    if t.startswith('ya29.'): return 'access_token'
    if t.startswith('1//') or re.match(r'^1/[A-Za-z0-9_-]{20,}$',t): return 'refresh_token'
    if re.match(r'^4/[A-Za-z0-9._/-]{10,}$',t) or re.match(r'^4%2F',t,re.I): return 'oauth_authorization_code'
    if t.startswith('GOCSPX-'): return 'oauth_client_secret'
    if t.startswith('AIza'): return 'google_api_key'
    if re.fullmatch(r'[0-9]+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com',t): return 'oauth_client_id'
    if len(t.split('.'))==3 and all(re.fullmatch(r'[A-Za-z0-9_-]+',x or '') for x in t.split('.')): return 'jwt_like'
    if re.match(r'^https?://',t): return 'url'
    return 'unknown'

def classify(text):
    t=text.strip(); k=classify_once(t)
    if k!='unknown': return k,t
    try:
        dec=base64.b64decode(t+'='*((4-len(t)%4)%4),validate=False).decode('utf-8'); k2=classify_once(dec)
        if k2!='unknown': return 'base64_'+k2,dec
    except Exception: pass
    return 'unknown',t

def mistral_req(url,method='GET',payload=None,retries=7):
    headers={'Authorization':'Bearer '+MISTRAL,'Content-Type':'application/json'}; data=None if payload is None else json.dumps(payload).encode(); last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,data=data,method=method,headers=headers)
            with urllib.request.urlopen(q,timeout=70) as r:return json.loads(r.read().decode())
        except Exception as e:last=e;time.sleep(min(2**i,15))
    raise last

def mistral_agent(kind, previous_failure):
    page=mistral_req('https://api.mistral.ai/v1/agents/pages'); agents=page.get('data',page if isinstance(page,list) else [])
    def score(a):
        s=((a.get('name')or'')+' '+(a.get('description')or'')).lower(); return sum(x in s for x in ('migra','preserv','transfer','soberan','interop'))
    agents=sorted(agents,key=score,reverse=True); agent=agents[0] if agents and score(agents[0]) else None
    if not agent:
        agent=mistral_req('https://api.mistral.ai/v1/agents','POST',{'model':'mistral-small-latest','name':'MILK Migration Preservative Executor','description':'Migração preservativa Drive para PTServidor por FTPS.','instructions':'Nunca veja nem peça valores de segredos. Preserve Drive read-only. Não invente tipos de credencial.'})
    allowed={'service_account_json','authorized_user_json','oauth_token_json','oauth_refresh_json','rclone_config','access_token','refresh_token'}
    if kind.startswith('base64_'): deterministic=kind[len('base64_'):]
    else: deterministic=kind
    prompt=(f'Nova execução. Classificação estrutural determinística da credencial opaca: {kind}. Falha anterior: {previous_failure}. '
            'Não tens acesso ao valor. Não contradigas a classificação determinística. Se o tipo for directamente utilizável pelo rclone, responde ACTION=USE_CLASSIFIED. '
            'Se for oauth_authorization_code, oauth_client_secret, oauth_client_id, google_api_key, oauth_client_json, jwt_like, url ou unknown, responde ACTION=NEEDS_PAIRING e indica apenas REQUIRED=<nomes dos componentes em falta>, sem pedir valores. '
            'Objectivo: Drive read-only -> FTPS TLS -> download verification.')
    conv=mistral_req('https://api.mistral.ai/v1/conversations','POST',{'agent_id':agent['id'],'inputs':prompt}); text=' '.join(str(o.get('content','')) for o in conv.get('outputs',[]) if isinstance(o,dict))
    action='USE_CLASSIFIED' if deterministic in allowed else 'NEEDS_PAIRING'
    m=re.search(r'ACTION=(USE_CLASSIFIED|NEEDS_PAIRING)',text,re.I)
    if m: action=m.group(1).upper()
    required=''; m2=re.search(r'REQUIRED=([^\n\r]+)',text,re.I)
    if m2: required=re.sub(r'[^A-Za-z0-9_, +.-]','',m2.group(1))[:240]
    receipt={'agent_id':agent['id'],'agent_name':agent.get('name'),'credential_class':kind,'action':action,'required':required,'secret_value_seen':False}
    (RUNNER/'mistral-agent-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    comment(f"MISTRAL_AGENT_ORCHESTRATED agent={agent.get('name')} class={kind} action={action} required={required or 'none'} secret_value_seen=no")
    return action,deterministic,required

def configure_drive(kind,norm):
    cfg=pathlib.Path.home()/'.config/rclone/rclone.conf'; cfg.parent.mkdir(parents=True,exist_ok=True)
    if kind=='rclone_config': cfg.write_text(norm)
    elif kind=='service_account_json':
        p=RUNNER/'gdrive-sa.json';p.write_text(norm);os.chmod(p,0o600);run(['rclone','config','create','gdrive','drive','service_account_file',str(p),'scope','drive.readonly','--non-interactive'],capture=True)
    elif kind=='authorized_user_json':
        d=json.loads(norm);tok=json.dumps({'access_token':'','token_type':'Bearer','refresh_token':d['refresh_token'],'expiry':'2000-01-01T00:00:00Z'});cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\nclient_id = '+d['client_id']+'\nclient_secret = '+d['client_secret']+'\ntoken = '+tok+'\n')
    elif kind=='oauth_token_json': cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+json.dumps(json.loads(norm),separators=(',',':'))+'\n')
    elif kind=='oauth_refresh_json':
        d=json.loads(norm);tok=json.dumps({'access_token':'','token_type':'Bearer','refresh_token':d['refresh_token'],'expiry':'2000-01-01T00:00:00Z'});out='[gdrive]\ntype = drive\nscope = drive.readonly\n';out+=('client_id = '+d['client_id']+'\n') if d.get('client_id') else '';out+=('client_secret = '+d['client_secret']+'\n') if d.get('client_secret') else '';out+='token = '+tok+'\n';cfg.write_text(out)
    elif kind=='access_token':
        exp=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=45)).isoformat().replace('+00:00','Z');tok=json.dumps({'access_token':norm.strip(),'token_type':'Bearer','refresh_token':'','expiry':exp});cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+tok+'\n')
    elif kind=='refresh_token':
        tok=json.dumps({'access_token':'','token_type':'Bearer','refresh_token':norm.strip(),'expiry':'2000-01-01T00:00:00Z'});cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+tok+'\n')
    else: raise RuntimeError('classified credential is not directly usable')
    try:os.chmod(cfg,0o600)
    except:pass
    remotes=[x.strip() for x in run(['rclone','listremotes'],capture=True).stdout.splitlines() if x.strip()]; remote=None
    for r in remotes:
        p=run(['rclone','config','show',r.rstrip(':')],check=False,capture=True)
        if p.returncode==0 and re.search(r'^type\s*=\s*drive\s*$',p.stdout,re.M):remote=r;break
    if not remote:raise RuntimeError('no Drive remote after credential setup')
    run(['rclone','lsd',remote,'--max-depth','1'],capture=True);comment('GDRIVE_READONLY_AUTH_OK remote_configured=yes drive_writes=0');return remote

def ftps_canary():
    src=RUNNER/'canary.bin';back=RUNNER/'canary.back';src.write_bytes(os.urandom(4096));sha=hashlib.sha256(src.read_bytes()).hexdigest();name=f'.milk-mistral-{os.environ.get("GITHUB_RUN_ID","run")}.bin';url=f'ftp://{FTPS_HOST}:{FTPS_PORT}/{name}';base=['curl','--fail','--silent','--show-error','--ssl-reqd','--ftp-pasv','--user',f'{FTPS_USER}:{FTPS_PASSWORD}']
    run(base+['-T',str(src),url]);run(base+[url,'-o',str(back)]);assert hashlib.sha256(back.read_bytes()).hexdigest()==sha;run(base+['-Q',f'DELE /{name}',f'ftp://{FTPS_HOST}:{FTPS_PORT}/'],check=False);comment(f'FTPS_CANARY_VERIFIED host={FTPS_HOST} bytes=4096 sha256={sha}')

def main():
    comment(f'MISTRAL_MIGRATION_EXECUTOR_STARTED run={os.environ.get("GITHUB_RUN_ID")} drive_writes=0')
    if not MISTRAL or not DRIVE_SECRET or not FTPS_PASSWORD:raise RuntimeError('required opaque secret missing')
    comment(f'OPAQUE_SECRETS_PRESENT mistral=yes drive=yes ftps=yes nextcloud={"yes" if NEXTCLOUD else "no"}')
    kind,norm=classify(DRIVE_SECRET);comment(f'DRIVE_CREDENTIAL_CLASSIFIED kind={kind} value_disclosed=no')
    action,direct,required=mistral_agent(kind,'previous service-account adapter rejected by Google: non-JSON credential')
    if action!='USE_CLASSIFIED':raise RuntimeError(f'credential_pairing_required class={kind} required={required or "unspecified"}')
    remote=configure_drive(direct,norm);ftps_canary();obsc=run(['rclone','obscure',FTPS_PASSWORD],capture=True).stdout.strip();run(['rclone','config','create','ptftps','ftp','host',FTPS_HOST,'port',FTPS_PORT,'user',FTPS_USER,'pass',obsc,'explicit_tls','true','--non-interactive'],capture=True);run(['rclone','lsd','ptftps:'],capture=True);comment('PTSERVIDOR_FTPS_AUTH_OK')
    src=json.loads(run(['rclone','size',remote,'--json'],capture=True).stdout);(RUNNER/'source-size.json').write_text(json.dumps(src,indent=2));comment(f"SOURCE_DISCOVERED objects={src.get('count')} bytes={src.get('bytes')} drive_writes=0")
    run(['rclone','copy',remote,'ptftps:','--fast-list','--transfers','6','--checkers','12','--retries','6','--low-level-retries','20','--create-empty-src-dirs','--log-file',str(RUNNER/'rclone-migration.log'),'--log-level','INFO']);comment('TRANSFER_COMPLETE_PENDING_DOWNLOAD_VERIFICATION drive_writes=0')
    run(['rclone','check',remote,'ptftps:','--one-way','--download','--checkers','8','--retries','4','--log-file',str(RUNNER/'rclone-check.log'),'--log-level','INFO']);dst=json.loads(run(['rclone','size','ptftps:','--json'],capture=True).stdout);(RUNNER/'dest-size.json').write_text(json.dumps(dst,indent=2));r={'state':'MIGRATION_VERIFIED','source_objects':src.get('count'),'source_bytes':src.get('bytes'),'destination_objects':dst.get('count'),'destination_bytes':dst.get('bytes'),'failed':0,'drive_writes':0,'verification':'rclone check --download'};(RUNNER/'migration-receipt.json').write_text(json.dumps(r,indent=2));comment(f"MIGRATION_VERIFIED source_objects={r['source_objects']} source_bytes={r['source_bytes']} destination_objects={r['destination_objects']} destination_bytes={r['destination_bytes']} failed=0 drive_writes=0")

try:main()
except Exception as e:
    comment('MISTRAL_MIGRATION_FAILED drive_writes=0 cause='+str(e).replace('\n',' ')[:700]);raise
