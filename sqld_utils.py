from sqlitedict import SqliteDict #Make sure to install it 
import os, json
import zlib, pickle, sqlite3

def open_sqld(sqld_fpath,encode_fn=json.dumps, decode_fn=json.loads,create=False,autocommit=True):
  if not create and not os.path.exists(sqld_fpath): return None #if the file doesn't exist and not to be created, return none
  mydict = SqliteDict(sqld_fpath, encode=encode_fn, decode=decode_fn, autocommit=autocommit)
  return mydict


def get_sqld_val(sqld_fpath,key):
  if not os.path.exists(sqld_fpath): return None
  mydict = SqliteDict(sqld_fpath, encode=json.dumps, decode=json.loads, autocommit=True)
  val=mydict.get(key)
  mydict.close()
  return val

def get_sqld_val_multiple(sqld_fpath,key_list):
  if not os.path.exists(sqld_fpath): return None
  output_dict={}
  mydict = SqliteDict(sqld_fpath, encode=json.dumps, decode=json.loads, autocommit=True)
  for key in key_list:
    val=mydict.get(key)
    if val==None: continue
    output_dict[key]=val
  mydict.close()
  return output_dict


def update_sqld_val(sqld_fpath,key,val,overwrite=True):
  output={}
  mydict = SqliteDict(sqld_fpath, encode=json.dumps, decode=json.loads, autocommit=True)
  output["key"]=key
  old_val=mydict.get(key)
  output["old"]=old_val
  output["new"]=val
  if overwrite==False and old_val!=None: output["success"]=False
  else:
    mydict[key]=val
    output["success"]=True
  mydict.close()
  return output

def update_sqld_multiple(sqld_fpath,key_val_list,overwrite=True):
  list_output=[]
  mydict = SqliteDict(sqld_fpath, encode=json.dumps, decode=json.loads, autocommit=False)
  for key,val in key_val_list:
    output={}
    output["key"]=key
    old_val=mydict.get(key)
    output["old"]=old_val
    output["new"]=val
    if overwrite==False and old_val!=None: output["success"]=False
    else:
      mydict[key]=val
      output["success"]=True
    list_output.append(output)
  mydict.commit()    
  mydict.close()
  return list_output

def dict2sqld(input_dict,sqld_fpath):
    sql_dict0 = SqliteDict(sqld_fpath,encode=json.dumps, decode=json.loads, autocommit=False)
    for key0,val0 in input_dict.items():
        sql_dict0[key0]=val0
    sql_dict0.commit()
    sql_dict0.close()
    return True   

def my_encode(obj):
    return sqlite3.Binary(zlib.compress(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)))

def my_decode(obj):
    return pickle.loads(zlib.decompress(bytes(obj)))    