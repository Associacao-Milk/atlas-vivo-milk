#!/usr/bin/env python3
import os, json, base64, re, subprocess, pathlib, urllib.request, time, hashlib, tempfile, datetime

RUNNER = pathlib.Path(os.environ.get('RUNNER_TEMP','/tmp'))
MISTRAL = os.environ.get('MISTRAL_API_KEY','')
DRIVE_SECRET = os.environ.get('DRIVE_SOMOSTODOSPOSSIVEIS','')
FTPS_PASSWORD = os.environ.get('PTSERVIDOR_FTPS_PASSWORD','')
NEXTCLOUD = os.environ.get('NEXTCLOUD_KEY','')
GH_TOKEN = os.environ.get('GH_TOKEN','')
REPO = os.environ.get('GITHUB_REPOSITORY','milkivc/atlas-vivo-milk')
ISSUE = os.environ.get('ISSUE_NUMBER','')
FTPS_HOST='troi.ptservidor.net'; FTPS_PORT='21'; FTPS_USER='migration@associacaomilk.pt'

def comment(msg):
    print(msg, flush=True)
    if not (GH_TOKEN and ISSUE): return
    data=json.dumps({'body':msg}).encode()
    req=urllib.request.Request(f'https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments',data=data,method='POST',headers={'Authorization':'Bearer '+GH_TOKEN,'Content-Type':'application/json','Accept':'application/vnd.github+json'})
    try: urllib.request.urlopen(req,timeout=30).read()
    except Exception as e: print('COMMENT_FAILED '+type(e).__name__, flush=True)

def run(args, check=True, capture=False, env=None):
    p=subprocess.run(args,check=False,text=True,capture_output=capture,env=env)
    if check and p.returncode!=0:
        detail=(p.stderr or p.stdout or '')[-800:].replace('\n',' ')
        raise RuntimeError(f'command_failed rc={p.returncode} detail={detail}')
    return p

def classify(text):
    t=text.strip()
    try:
        d=json.loads(t)
        if isinstance(d,dict):
            if d.get('type')=='service_account' and d.get('private_key') and d.get('client_email'): return 'service_account_json',t
            if d.get('type')=='authorized_user' and all(d.get(k) for k in ('client_id','client_secret','refresh_token')): return 'authorized_user_json',t
            if d.get('refresh_token') and d.get('access_token'): return 'oauth_token_json',t
            if d.get('refresh_token'): return 'oauth_refresh_json',t
            if 'installed' in d or 'web' in d: return 'oauth_client_json',t
    except Exception: pass
    if re.search(r'^\s*\[[^]]+\]\s*$',t,re.M) and re.search(r'^\s*type\s*=\s*drive\s*$',t,re.M): return 'rclone_config',t
    if t.startswith('ya29.'): return 'access_token',t
    if t.startswith('1//'): return 'refresh_token',t
    try:
        dec=base64.b64decode(t+'='*((4-len(t)%4)%4),validate=False).decode('utf-8')
        k,n=classify(dec)
        if k!='unknown': return k,n
    except Exception: pass
    return 'unknown',t

def mistral_req(url,method='GET',payload=None,retries=7):
    headers={'Authorization':'Bearer '+MISTRAL,'Content-Type':'application/json'}
    data=None if payload is None else json.dumps(payload).encode()
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,data=data,method=method,headers=headers)
            with urllib.request.urlopen(req,timeout=70) as r: return json.loads(r.read().decode())
        except Exception as e:
            last=e; time.sleep(min(2**i,15))
    raise last

def mistral_agent_decide(kind):
    page=mistral_req('https://api.mistral.ai/v1/agents/pages')
    agents=page.get('data',page if isinstance(page,list) else [])
    def score(a):
        s=((a.get('name') or '')+' '+(a.get('description') or '')).lower()
        return sum(w in s for w in ('migra','preserv','transfer','soberan','interop'))
    agents=sorted(agents,key=score,reverse=True)
    if agents and score(agents[0])>0:
        agent=agents[0]
    else:
        agent=mistral_req('https://api.mistral.ai/v1/agents','POST',{
            'model':'mistral-small-latest','name':'MILK Migration Preservative Executor',
            'description':'Executor soberano de migração preservativa Google Drive para PTServidor por FTPS.',
            'instructions':'Nunca peça, revele ou repita segredos. Trabalhe apenas com classificações opacas e recibos. Google Drive é estritamente read-only. Exija canário FTPS e download verification antes de declarar conclusão.'})
    prompt=(f'Credencial DRIVE opaca classificada como {kind}. Mistral, FTPS e Nextcloud presentes={bool(NEXTCLOUD)}. '
            'Escolha APENAS um adaptador: service_account_json, authorized_user_json, oauth_token_json, oauth_refresh_json, rclone_config, access_token, refresh_token, oauth_client_json, probe_all_safe. '
            'Nunca peça valores nem intervenção humana. Objectivo: Google Drive read-only -> FTPS explícito TLS -> verificação por download. Responda ACTION=<adaptador>.')
    conv=mistral_req('https://api.mistral.ai/v1/conversations','POST',{'agent_id':agent['id'],'inputs':prompt})
    text=' '.join(str(o.get('content','')) for o in conv.get('outputs',[]) if isinstance(o,dict))
    m=re.search(r'ACTION=([a-z0-9_]+)',text,re.I)
    safe={'service_account_json','authorized_user_json','oauth_token_json','oauth_refresh_json','rclone_config','access_token','refresh_token','oauth_client_json','probe_all_safe'}
    action=m.group(1).lower() if m else kind
    if action not in safe: action=kind if kind in safe else 'probe_all_safe'
    receipt={'agent_id':agent['id'],'agent_name':agent.get('name'),'credential_class':kind,'action':action,'secret_value_seen':False}
    (RUNNER/'mistral-agent-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    comment(f"MISTRAL_AGENT_ORCHESTRATED agent={agent.get('name')} action={action} secret_value_seen=no")
    return action

def configure_drive(kind, normalized, action):
    cfg=pathlib.Path.home()/'.config/rclone/rclone.conf'; cfg.parent.mkdir(parents=True,exist_ok=True)
    action=kind if action=='probe_all_safe' else action
    if action=='rclone_config': cfg.write_text(normalized,encoding='utf-8')
    elif action=='service_account_json':
        p=RUNNER/'gdrive-sa.json'; p.write_text(normalized,encoding='utf-8'); os.chmod(p,0o600)
        run(['rclone','config','create','gdrive','drive','service_account_file',str(p),'scope','drive.readonly','--non-interactive'],capture=True)
    elif action=='authorized_user_json':
        d=json.loads(normalized); tok=json.dumps({'access_token':'','token_type':'Bearer','refresh_token':d['refresh_token'],'expiry':'2000-01-01T00:00:00Z'})
        cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\nclient_id = '+d['client_id']+'\nclient_secret = '+d['client_secret']+'\ntoken = '+tok+'\n')
    elif action=='oauth_token_json': cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+json.dumps(json.loads(normalized),separators=(',',':'))+'\n')
    elif action=='oauth_refresh_json':
        d=json.loads(normalized); tok=json.dumps({'access_token':'','token_type':'Bearer','refresh_token':d['refresh_token'],'expiry':'2000-01-01T00:00:00Z'}); out='[gdrive]\ntype = drive\nscope = drive.readonly\n'; out+=('client_id = '+d['client_id']+'\n') if d.get('client_id') else ''; out+=('client_secret = '+d['client_secret']+'\n') if d.get('client_secret') else ''; out+='token = '+tok+'\n'; cfg.write_text(out)
    elif action=='access_token':
        exp=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=45)).isoformat().replace('+00:00','Z'); tok=json.dumps({'access_token':normalized.strip(),'token_type':'Bearer','refresh_token':'','expiry':exp}); cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+tok+'\n')
    elif action=='refresh_token':
        tok=json.dumps({'access_token':'','token_type':'Bearer','refresh_token':normalized.strip(),'expiry':'2000-01-01T00:00:00Z'}); cfg.write_text('[gdrive]\ntype = drive\nscope = drive.readonly\ntoken = '+tok+'\n')
    elif action=='oauth_client_json': raise RuntimeError('OAuth client definition has no user authorization token')
    else: raise RuntimeError('unsupported credential format after Mistral probe')
    try: os.chmod(cfg,0o600)
    except Exception: pass
    remotes=[x.strip() for x in run(['rclone','listremotes'],capture=True).stdout.splitlines() if x.strip()]
    drive_remote=None
    for r in remotes:
        p=run(['rclone','config','show',r.rstrip(':')],check=False,capture=True)
        if p.returncode==0 and re.search(r'^type\s*=\s*drive\s*$',p.stdout,re.M): drive_remote=r; break
    if not drive_remote and remotes: drive_remote=remotes[0]
    if not drive_remote: raise RuntimeError('no rclone Drive remote')
    run(['rclone','lsd',drive_remote,'--max-depth','1'],capture=True)
    comment('GDRIVE_READONLY_AUTH_OK remote_configured=yes drive_writes=0')
    return drive_remote

def ftps_canary():
    src=RUNNER/f'canary-{os.environ.get("GITHUB_RUN_ID","run")}.bin'; back=RUNNER/'canary.back.bin'; src.write_bytes(os.urandom(4096)); sha=hashlib.sha256(src.read_bytes()).hexdigest(); name='.'+src.name; url=f'ftp://{FTPS_HOST}:{FTPS_PORT}/{name}'
    base=['curl','--fail','--silent','--show-error','--ssl-reqd','--ftp-pasv','--connect-timeout','20','--max-time','120','--user',f'{FTPS_USER}:{FTPS_PASSWORD}']
    run(base+['-T',str(src),url]); run(base+[url,'-o',str(back)])
    if hashlib.sha256(back.read_bytes()).hexdigest()!=sha: raise RuntimeError('FTPS SHA256 mismatch')
    run(base+['-Q',f'DELE /{name}',f'ftp://{FTPS_HOST}:{FTPS_PORT}/'],check=False)
    comment(f'FTPS_CANARY_VERIFIED host={FTPS_HOST} bytes=4096 sha256={sha}')

def main():
    comment(f'MISTRAL_MIGRATION_EXECUTOR_STARTED run={os.environ.get("GITHUB_RUN_ID")} drive_writes=0')
    if not MISTRAL: raise RuntimeError('MISTRAL_API_KEY missing')
    if not DRIVE_SECRET: raise RuntimeError('DRIVE_SOMOSTODOSPOSSIVEIS missing')
    if not FTPS_PASSWORD: raise RuntimeError('PTSERVIDOR_FTPS_PASSWORD missing')
    comment(f'OPAQUE_SECRETS_PRESENT mistral=yes drive=yes ftps=yes nextcloud={"yes" if NEXTCLOUD else "no"}')
    kind,norm=classify(DRIVE_SECRET); comment(f'DRIVE_CREDENTIAL_CLASSIFIED kind={kind} value_disclosed=no')
    action=mistral_agent_decide(kind)
    remote=configure_drive(kind,norm,action)
    ftps_canary()
    obsc=run(['rclone','obscure',FTPS_PASSWORD],capture=True).stdout.strip()
    run(['rclone','config','create','ptftps','ftp','host',FTPS_HOST,'port',FTPS_PORT,'user',FTPS_USER,'pass',obsc,'explicit_tls','true','--non-interactive'],capture=True)
    run(['rclone','lsd','ptftps:'],capture=True); comment(f'PTSERVIDOR_FTPS_AUTH_OK host={FTPS_HOST}')
    src=json.loads(run(['rclone','size',remote,'--json'],capture=True).stdout); (RUNNER/'source-size.json').write_text(json.dumps(src,indent=2)); comment(f"SOURCE_DISCOVERED objects={src.get('count')} bytes={src.get('bytes')} drive_writes=0")
    run(['rclone','copy',remote,'ptftps:','--fast-list','--transfers','6','--checkers','12','--retries','6','--low-level-retries','20','--create-empty-src-dirs','--log-file',str(RUNNER/'rclone-migration.log'),'--log-level','INFO'])
    comment('TRANSFER_COMPLETE_PENDING_DOWNLOAD_VERIFICATION drive_writes=0')
    run(['rclone','check',remote,'ptftps:','--one-way','--download','--checkers','8','--retries','4','--log-file',str(RUNNER/'rclone-check.log'),'--log-level','INFO'])
    dst=json.loads(run(['rclone','size','ptftps:','--json'],capture=True).stdout); (RUNNER/'dest-size.json').write_text(json.dumps(dst,indent=2)); receipt={'state':'MIGRATION_VERIFIED','source_objects':src.get('count'),'source_bytes':src.get('bytes'),'destination_objects':dst.get('count'),'destination_bytes':dst.get('bytes'),'failed':0,'drive_writes':0,'verification':'rclone check --download'}; (RUNNER/'migration-receipt.json').write_text(json.dumps(receipt,indent=2)); comment(f"MIGRATION_VERIFIED source_objects={receipt['source_objects']} source_bytes={receipt['source_bytes']} destination_objects={receipt['destination_objects']} destination_bytes={receipt['destination_bytes']} failed=0 drive_writes=0")

try: main()
except Exception as e:
    msg=str(e).replace('\n',' ')[:700]
    comment('MISTRAL_MIGRATION_FAILED drive_writes=0 cause='+msg)
    raise
