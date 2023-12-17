import pandas as pd
import math

def get_sheet_list(sheet_obj,key_col0,val_col0): #pandas get conversion dicts
  #tmp_sheet_dict={}
  tmp_sheet_list=[]

  for i0,row0 in sheet_obj.iterrows():
    cur_key,cur_val=row0[key_col0],row0[val_col0]
    if cur_key=="" or cur_val=="": continue
    tmp_sheet_list.append((cur_key,cur_val))
    #tmp_sheet_dict[cur_key]=cur_val
  return tmp_sheet_list

def get_workbook_obj(path0,dtype0=str):
  return pd.read_excel(path0, None,keep_default_na=False,dtype=dtype0)

def get_sheet_obj(wb_obj,sheet):
  return wb_obj[sheet]


#17 Dec 23
#get arbitrary keys and values from the sheet content by specifying key column(s) and val column(s)
def get_sheet_keys_values(sheet_obj,key_cols,val_cols,join_key_by="|"):
  key_val_dict={}
  for i0,row_dict0 in sheet_obj.iterrows():
    cur_keys=[row_dict0.get(k,"") for k in key_cols]
    cur_vals=[row_dict0.get(k,"") for k in val_cols]
    key_str0=join_key_by.join(cur_keys)
    key_val_dict[key_str0]=cur_vals
  return key_val_dict


def get_wb_sheet_list(path1,sheet1,key_col1,val_col1):
  wb_obj1=get_workbook_obj(path1)
  sheet_obj1=wb_obj1[sheet1]
  sheet_key_val_list1=get_sheet_list(sheet_obj1,key_col1,val_col1)
  return sheet_key_val_list1

def get_xls_sheet_col_data(xls_fpath0,sheet_name0,col_names0,default_val0=0.,exclude_nan=False):
  wb_obj0=get_workbook_obj(xls_fpath0)
  pd_frame0=wb_obj0[sheet_name0]
  all_col_data=[]
  for index0,row_dict0 in pd_frame0.iterrows():
    cur_list=[row_dict0.get(v,default_val0) for v in col_names0]
    valid_row=True
    for cl in cur_list: 
      if exclude_nan and math.isnan(cl): valid_row=False
    if not valid_row: continue
    all_col_data.append(cur_list)
  return all_col_data  

def get_sheets_cols(wb_obj0,sheet_names0,col_names0,apply_str=True,exclude_nan=True, exclude_empty=True,default_val0=""):
  all_col_data=[]
  for sh0 in sheet_names0:
    cur_sheet0=wb_obj0[sh0]
    for index0,row_dict0 in cur_sheet0.iterrows():
      cur_list=[row_dict0.get(v,default_val0) for v in col_names0]
      valid_row=True
      for cl in cur_list: 
        if apply_str: cl=str(cl)
        #print(cl, type(cl))
        #if not type(cl) is str: cl=str(cl) 
        #if exclude_nan and math.isnan(cl): valid_row=False
        if exclude_empty and cl=="": valid_row=False
      if not valid_row: continue
      all_col_data.append(cur_list)
  return all_col_data


def get_wb_data(wb_fpath,dtype0=str):
  wb_data_list0=[]
  wb_obj0=pd.read_excel(wb_fpath, None,keep_default_na=False,dtype=dtype0)
  sheet_names0=list(wb_obj0.keys())
  for sh0 in sheet_names0:
    sheet_data_list=[]
    cur_sheet0=wb_obj0[sh0]
    for index0,row_dict0 in cur_sheet0.iterrows():
      tmp_row_dict={}
      for a,b in dict(row_dict0).items(): tmp_row_dict[a.strip()]=b.strip()
      sheet_data_list.append(tmp_row_dict)

    wb_data_list0.append(sheet_data_list)
  return wb_data_list0


def get_wb_data_dict(wb_fpath,dtype0=str): #same as above, but data output is in dict format, keys are sheet names
  wb_data_dict0={}
  wb_obj0=pd.read_excel(wb_fpath, None,keep_default_na=False,dtype=dtype0)
  sheet_names0=list(wb_obj0.keys())
  for sh0 in sheet_names0:
    sheet_data_list=[]
    cur_sheet0=wb_obj0[sh0]
    for index0,row_dict0 in cur_sheet0.iterrows():
      tmp_row_dict={}
      for a,b in dict(row_dict0).items(): tmp_row_dict[a.strip()]=b.strip()
      sheet_data_list.append(tmp_row_dict)
    #wb_data_list0.append(sheet_data_list)
    wb_data_dict0[sh0.strip()]=sheet_data_list
  return wb_data_dict0



if __name__=="__main__":
  print("Hello")
