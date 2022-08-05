#!/usr/bin/env python
import os, sys, time
import concurrent.futures
#import urllib.request

def gen_url_list(fname,start_i=0,n_pages=50,exclude_dict={}):
  fopen=open(fname)
  for li,line in enumerate(fopen):
    if line=="": 
      fopen.close()
      return
    if li<start_i: continue
    if li>=start_i+n_pages: break
    cur_url=line.strip("\n\r")
    if exclude_dict.get(cur_url)==True: continue
    yield cur_url
  fopen.close()


def get_cached_urls(cache_fpath):
  cached_url_dict={}
  if os.path.exists(cache_fpath):
    cached_fopen=open(cache_fpath)
    for i,f in enumerate(cached_fopen):
      url=f.split("<br>")[0]
      if not url.startswith("http"): continue
      cached_url_dict[url]=True
    cached_fopen.close()
  return cached_url_dict

# n_urls=file_len(url_list_fpath)
# print("number of urls to process:",n_urls)

def multi_url_caching(url_list_fpath0,cached_content_fpath0,batch_size=1000,max_n_workers=30,start_i=0):
  #batch_size=1000
  n_urls=file_len(url_list_fpath0)
  cached_url_dict0=get_cached_urls(cached_content_fpath0)
  print("number of urls to process:",n_urls)
  end_i=n_urls#-start_i
  print("start_i",start_i, "end_i",end_i, "n_urls",n_urls)
  t0_=time.time()
  for i_ in range(start_i,end_i,batch_size): #the end number should be the size of the file being read
    t1_=time.time()
    print("current i",i_, "time:", round(t1_-t0_,2) )
    t0_=time.time()
    URLS=gen_url_list(url_list_fpath0,i_,batch_size,cached_url_dict0)

    # We can use a with statement to ensure threads are cleaned up promptly
    content_list=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_n_workers) as executor:
        # Start the load operations and mark each future with its URL
        #future_to_url = {executor.submit(load_url, url, 60): url for url in URLS}
        future_to_url = {executor.submit(get_content, url): url for url in URLS if cached_url_dict0.get(url)!=True}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            #if len(content_list)>8000: print(len(content_list),url)
            #print(url)
            try:
                data = future.result()
            except Exception as exc:
                #print('%r generated an exception: %s' % (url, exc))
                pass
            else:
                #print('%r page is %d bytes' % (url, len(data)))
                content_list.append(data)
                if len(content_list)%1000==0: print("current content list length",url, len(content_list))
                
                #print(len(content_list))
    cached_content_fopen=open(cached_content_fpath0,"a")
    
    for cl in content_list:
      try: cached_content_fopen.write(cl+"\n")
      except: cached_content_fopen.write("\n")
    cached_content_fopen.close()
if __name__=="__main__":
  crawl_dir="crawl"
  run_dir="aug21" #aug21_au
  run_dir="oct21_nz"
  url_list_fname="all_urls.txt"
  cached_content_fname="cached_all.txt"
  
  cur_batch_size=10000
  cur_max_n_workers=60
  cur_start_i=0
  main_dir_path=os.path.join(crawl_dir,run_dir)
  url_list_fpath=os.path.join(main_dir_path,url_list_fname) #"all_au_urls.txt"
  cached_content_fpath=os.path.join(main_dir_path,cached_content_fname) #"cached_all_au.txt"


  cur_url_list_fpath="oct21_nz/all_urls.txt"
  cur_cached_content_fpath="oct21_nz/cached_all.txt"
  if len(sys.argv)>2: 
    url_list_fpath=sys.argv[1]
    cached_content_fpath=sys.argv[2]
  if len(sys.argv)>3: cur_batch_size=int(sys.argv[3]) 
  if len(sys.argv)>4: cur_max_n_workers=int(sys.argv[4]) 
  if len(sys.argv)>5: cur_start_i=int(sys.argv[5]) 
  
  #print(os.getcwd())
  print("cur_batch_size",cur_batch_size)
  print("cur_max_n_workers",cur_max_n_workers)
  print("cur_start_i",cur_start_i)
  sys.path.append("utils")
  #print(sys.version)
  from extraction_utils import *
  print("processing URL list: ",url_list_fpath)
  print("Output cached file: ",cached_content_fpath)


  # url_list_fname="gov.au.txt"
  # cached_content_fname="cached_gov11.txt"
  
  t0=time.time()
  i0=0
  #i0=370000
  multi_url_caching(url_list_fpath,cached_content_fpath,batch_size=cur_batch_size,max_n_workers=cur_max_n_workers,start_i=cur_start_i)
  t1=time.time()
  elapsed=t1-t0
  print("completed in %s seconds"%elapsed)
