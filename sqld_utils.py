from sqlitedict import SqliteDict #Make sure to install it 
def get_sqld_val(sqld_fpath,key):
  if not os.path.exists(sqld_fpath): return None
  mydict = SqliteDict(sqld_fpath, autocommit=True)
  val=mydict.get(key)
  mydict.close()
  return val

def update_sqld_val(sqld_fpath,key,val,overwrite=True):
  output={}
  mydict = SqliteDict(sqld_fpath, autocommit=True)
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
  mydict = SqliteDict(sqld_fpath, autocommit=True)
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
  mydict.close()
  return list_output