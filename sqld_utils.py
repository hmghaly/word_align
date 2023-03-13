from sqlitedict import SqliteDict #Make sure to install it 
import os, json

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