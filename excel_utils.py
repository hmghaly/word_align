from openpyxl import Workbook, load_workbook

def xl_read_sheet(wb_obj,sheet_name):
  cur_sheet=wb_obj[sheet_name]
  headers=[]
  sheet_data=[]
  for i0,row0 in enumerate(cur_sheet.iter_rows()):
    row_vals=[v.value for v in row0]
    if i0==0: headers=row_vals
    else: 
      row_dict0=dict(iter(zip(headers,row_vals)))
      sheet_data.append(row_dict0)
  return sheet_data

def xl_read_all_sheets(wb_obj,sheet_name_list=None):
  if sheet_name_list==None: sheet_name_list=wb_obj.sheetnames
  else: sheet_name_list=[v for v in wb_obj.sheetnames if v in sheet_name_list]
  wb_dict={}
  for sheet0 in sheet_name_list: wb_dict[sheet0]=xl_read_sheet(wb_obj,sheet0)
  return wb_dict

def xl_get_wb(wb_fpath): return load_workbook(wb_fpath)

def xl2data(wb_fpath,sheet_name_list=None): 
  wb_obj0=xl_get_wb(wb_fpath)
  return xl_read_all_sheets(wb_obj0,sheet_name_list=sheet_name_list)