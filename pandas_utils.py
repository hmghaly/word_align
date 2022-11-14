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

def get_workbook_obj(path0):
  return pd.read_excel(path0, None,keep_default_na=False)

def get_sheet_obj(wb_obj,sheet):
  return wb_obj[sheet]

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

if __name__=="__main__":
  print("Hello")
