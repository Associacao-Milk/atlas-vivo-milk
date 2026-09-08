#!/usr/bin/env python3
import os,json
rclone=os.environ.get('RCLONE_CONFIG_SECRET','').strip()
sa=os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON','').strip()
cid=os.environ.get('GOOGLE_CLIENT_ID','').strip()
cs=os.environ.get('GOOGLE_CLIENT_SECRET','').strip()
rt=os.environ.get('GOOGLE_REFRESH_TOKEN','').strip()
opaque=os.environ.get('DRIVE_SOMOSTODOSPOSSIVEIS','').strip()
source='none'; value=''
if rclone:
    source='RCLONE_CONFIG'; value=rclone
elif sa:
    source='SERVICE_ACCOUNT'; value=sa
elif cid and cs and rt:
    source='AUTHORIZED_USER_TRIPLE'; value=json.dumps({'type':'authorized_user','client_id':cid,'client_secret':cs,'refresh_token':rt},separators=(',',':'))
elif opaque:
    source='DRIVE_SOMOSTODOSPOSSIVEIS'; value=opaque
print(value,end='')
# Metadata goes to GITHUB_OUTPUT only; never the value.
out=os.environ.get('GITHUB_OUTPUT')
if out:
    with open(out,'a',encoding='utf-8') as f:f.write('source='+source+'\n')
