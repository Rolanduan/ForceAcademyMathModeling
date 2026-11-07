from pathlib import Path
import csv,hashlib,datetime,os,json,urllib.request,zipfile
from concurrent.futures import ThreadPoolExecutor
p=Path('v14_cloud_evidence');raw=p/'original';out=p/'derived';raw.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
G={'4805000','2507000','1714000','0820000','5548000','2743000','4261000','4159000','3755000','0666000','5363000','1304000'}
states=sorted({g[:2] for g in G})
base='https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData'
urls={f'ACS_{x}':f'{base}/acsdt5y2024-{x.lower()}.dat' for x in ['B01001','B25070','B19013','B08201']}
urls.update({f'TIGER_PLACE_{s}':f'https://www2.census.gov/geo/tiger/TIGER2024/PLACE/tl_2024_{s}_place.zip' for s in states})
urls['NCES_2024_25']='https://data-nces.opendata.arcgis.com/api/download/v1/items/10e02c7ba56b4ef4a6a050f212f75134/csv?layers=0'
urls['IMLS_FY2024']='https://www.imls.gov/sites/default/files/2026-06/pls_fy2024_csv.zip'
urls['COMAP_SUMMARY']='https://www.contest.comap.com/highschool/contests/himcm/flyers/HiMCM-MidMCM_Summary.tex'
def get(x):
 key,url=x;ext='.zip' if key.startswith(('TIGER','IMLS')) else '.dat' if key.startswith('ACS') else '.csv' if key.startswith('NCES') else '.tex'
 target=raw/(key+ext);r=dict(source_id=key,url=url,status='ERROR',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=95) as stream,target.open('wb') as f:
   r['http_status']=stream.status;h=hashlib.sha256();sz=0
   while True:
    chunk=stream.read(1048576)
    if not chunk:break
    f.write(chunk);h.update(chunk);sz+=len(chunk)
  with target.open('rb') as f:header=f.read(100).lower()
  if sz<500 or b'<html' in header:raise ValueError('invalid non-data response')
  if ext=='.zip' and not zipfile.is_zipfile(target):raise ValueError('invalid ZIP')
  if key.startswith('ACS') and not header.startswith(b'geo_id'):raise ValueError('unexpected ACS schema: '+repr(header))
  r.update(status='DOWNLOADED_ORIGINAL_WITH_SHA',sha256=h.hexdigest(),bytes=sz,local_path=str(target))
 except Exception as e:
  r['status']='FAILED '+repr(e)[:240]
  if target.exists():target.unlink()
 return r
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(get,urls.items()))
for r in results:
 print(r['source_id'],r['status'],r.get('bytes',0),flush=True)
 if r['status']=='DOWNLOADED_ORIGINAL_WITH_SHA' and r['source_id'].startswith('ACS'):
  try:
   src=Path(r['local_path']);tgt=out/(r['source_id']+'_12_city_rows.csv');n=0
   with src.open(encoding='utf-8-sig',newline='') as f,tgt.open('w',encoding='utf-8',newline='') as fo:
    reader=csv.DictReader(f);writer=csv.DictWriter(fo,reader.fieldnames);writer.writeheader()
    print('ACS_COLUMNS',r['source_id'],reader.fieldnames[:8],flush=True)
    for row in reader:
     geoid=row.get('GEO_ID','')
     if geoid.startswith('1600000US') and geoid[9:] in G:writer.writerow(row);n+=1
   r['cities_matched']=n
  except Exception as e:r['filter_error']=repr(e)
(out/'receipts.json').write_text(json.dumps(results,indent=2))
