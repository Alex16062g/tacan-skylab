"""Read tiled PDS TIFF windows over verified HTTPS byte-range requests."""
import io, socket, threading, os, tempfile, hashlib, time
from pathlib import Path
from email.utils import parsedate_to_datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache
import requests, tifffile, numpy as np

_original_dns=socket.getaddrinfo
COOLDOWN=Path(os.environ.get('LOCALAPPDATA',tempfile.gettempdir()))/'SpaceTerrainCache'/'pds-cooldown.txt'

class RateLimited(RuntimeError):pass

def retry_seconds(value, now=None):
    now=time.time() if now is None else now
    try:return max(1,int(value))
    except (ValueError,TypeError):
        try:return max(1,int(parsedate_to_datetime(value).timestamp()-now)+1)
        except (ValueError,TypeError,OverflowError):return 3600

def record_cooldown(value):
    seconds=retry_seconds(value)
    COOLDOWN.parent.mkdir(parents=True,exist_ok=True)
    previous=float(COOLDOWN.read_text()) if COOLDOWN.exists() else 0
    COOLDOWN.write_text(str(max(previous,time.time()+seconds)))
    return seconds

def range_request(session,url,headers):
    if COOLDOWN.exists():
        until=float(COOLDOWN.read_text())
        if time.time()<until:raise RateLimited(f'PDS retry after {time.strftime("%Y-%m-%d %H:%M:%S UTC",time.gmtime(until))}')
    r=session.get(url,headers=headers,timeout=(5,40))
    if r.status_code==429:
        seconds=record_cooldown(r.headers.get('Retry-After','3600'))
        raise RateLimited(f'PDS rate limit; retry after {seconds} seconds')
    r.raise_for_status();return r
def nasa_dns():
    host='pds.mcp.nasa.gov'
    records=requests.get('https://dns.google/resolve',params={'name':host,'type':'A'},timeout=10).json().get('Answer',[])
    addresses=[r['data'] for r in records if r['type']==1]
    if addresses:
        socket.getaddrinfo=lambda name,*args,**kw: [entry for ip in addresses for entry in _original_dns(ip,*args,**kw)] if name==host else _original_dns(name,*args,**kw)

class RemoteFile(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.name=url;self.position=0;self.session=requests.Session()
        self.session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=.5,status_forcelist=[500,502,503,504],respect_retry_after_header=False)))
        self.cache=Path(os.environ.get('LOCALAPPDATA',tempfile.gettempdir()))/'SpaceTerrainCache'/'pds-ranges'/hashlib.sha256(url.encode()).hexdigest()[:16]
        self.cache.mkdir(parents=True,exist_ok=True)
        r=range_request(self.session,url,{'Range':'bytes=0-15'})
        if r.status_code!=206:raise ValueError('Range support required')
        self.length=int(r.headers['Content-Range'].split('/')[-1])
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.position
    def seek(self,offset,whence=0):
        self.position=offset+(self.position if whence==1 else self.length if whence==2 else 0);return self.position
    @lru_cache(maxsize=128)
    def block(self,index):
        start=index*65536;end=min(self.length-1,start+65535)
        cached=self.cache/f'{index}.bin'
        if cached.exists() and cached.stat().st_size==end-start+1:return cached.read_bytes()
        r=range_request(self.session,self.url,{'Range':f'bytes={start}-{end}'})
        if r.status_code!=206 or len(r.content)!=end-start+1:raise ValueError('Invalid byte range')
        temporary=cached.with_suffix(f'.{os.getpid()}.part');temporary.write_bytes(r.content);os.replace(temporary,cached)
        return r.content
    def read(self,size=-1):
        size=min(size if size>=0 else self.length-self.position,self.length-self.position)
        out=[]
        while size>0:
            index,off=divmod(self.position,65536);data=self.block(index)[off:off+size]
            if not data:break
            out.append(data);self.position+=len(data);size-=len(data)
        return b''.join(out)

def window(page,reader,x0,y0,x1,y1):
    tw,th=page.tilewidth,page.tilelength
    result=np.zeros((y1-y0,x1-x0),dtype=page.dtype)
    across=(page.imagewidth+tw-1)//tw
    for ty in range(y0//th,(y1-1)//th+1):
        for tx in range(x0//tw,(x1-1)//tw+1):
            i=ty*across+tx;reader.seek(page.dataoffsets[i]);compressed=reader.read(page.databytecounts[i])
            tile,_,_=page.decode(compressed,i);tile=tile.reshape(th,tw)
            ax=max(x0,tx*tw);bx=min(x1,(tx+1)*tw);ay=max(y0,ty*th);by=min(y1,(ty+1)*th)
            result[ay-y0:by-y0,ax-x0:bx-x0]=tile[ay-ty*th:by-ty*th,ax-tx*tw:bx-tx*tw]
    return result

if __name__=='__main__':
    nasa_dns()
    url='https://pds.mcp.nasa.gov/data/store/img/lunar_reconnaissance_orbiter/pds4/lroc/lro-l-lroc-5-rdr/LROLRC_2001/EXTRAS/BROWSE/WAC_GLOBAL/WAC_GLOBAL_E300N0450_100M.PYR.TIF'
    f=RemoteFile(url)
    with tifffile.TiffFile(f) as t:
        print(t.geotiff_metadata,flush=True)
        print([(p.shape,p.tilewidth,p.tilelength) for p in t.pages],flush=True)
        a=window(t.pages[0],f,10940,10340,11080,10480)
        print(a.shape,a.min(),a.max(),flush=True)
