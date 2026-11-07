#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,os,urllib.parse,urllib.request,time
ROOT=Path('v14_cloud_evidence');DIR=ROOT/'acs_api_original';DIR.mkdir(parents=True,exist_ok=True)
CITIES={'4805000':'Austin','2507000':'Boston','1714000':'Chicago','0820000':'Denver','5548000':'Madison','2743000':'Minneapolis','4261000':'Pittsburgh','4159000':'Portland','3755000':'Raleigh','0666000':'San Diego','5363000':'Seattle','1304000':'Atlanta'}
V=['NAME','B01001_001E','B01001_006E','B01001_030E','B01001_006M','B01001_030M','B25070_001E','B25070_007E','B25070_008E','B25070_009E','B25070_010E','B25070_011E','B19013_001E','B19013_001M']
receipts=[]
for geoid,city in CITIES.items():
 p={'get':','.join(V),'for':'place:'+geoid[2:],'in':'state:'+geoid[:2]}
 if os.getenv('CENSUS_API_KEY'):p['key']=os.getenv('CENSUS_API_KEY')
 url='https://api.census.gov/data/2024/acs/acs5?'+urllib.parse.urlencode(p)
 dest=DIR/f'city_{geoid}.json';r=dict(city_geoid=geoid,city=city,url=url.split('&key=')[0],status='FAILED')
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Academic-Research/1.0'})
   with urllib.request.urlopen(req,timeout=45) as f:raw=f.read()
   arr=json.loads(raw)
   assert len(arr)==2
   row=dict(zip(arr[0],arr[1]))
   assert row['state']+row['place']==geoid
   assert int(row['B01001_006E'])+int(row['B01001_030E'])>0
   dest.write_bytes(raw)
   r.update(status='DOWNLOADED_ORIGINAL_WITH_SHA',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),local_path=str(dest))
   break
  except Exception as e:r['error']=str(e)[:200];time.sleep(1+attempt)
 receipts.append(r);print(city,r['status'],r.get('bytes',0),flush=True)
(ROOT/'derived').mkdir(parents=True,exist_ok=True)
(ROOT/'derived/acs_api_receipts.json').write_text(json.dumps(receipts,indent=2))
