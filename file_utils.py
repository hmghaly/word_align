import tempfile, shutil, os, time
def remove_line(str0,fpath0): #remove a line that starts with certin str
  tmp = tempfile.NamedTemporaryFile(delete=True)
  shutil.copy2(fpath0, tmp.name)
  write_fopen=open(fpath0,"w")
  tmp_fpath=tmp.name
  fopen=open(tmp_fpath)
  for li in fopen:
    if li.startswith(str0): pass
    else: write_fopen.write(li)
  fopen.close()
  write_fopen.close()

def get_line(line_i0,fpath0,line_size=100): #from a file with fixed line size
  if not os.path.exists(fpath0): return ""
  fopen0=open(fpath0)
  fopen0.seek(line_i0*line_size)
  cur_line=fopen0.readline().strip()
  fopen0.close()
  return cur_line

def get_multiple_lines(line_i0,n_lines,fpath0,line_size=100): #get n lines starting line #
  if not os.path.exists(fpath0): return []
  line_list=[]
  fopen0=open(fpath0)
  fopen0.seek(line_i0*line_size)
  for _ in range(n_lines):
    cur_line=fopen0.readline().strip()
    if cur_line: line_list.append(cur_line)
  fopen0.close()
  return line_list

def get_file_n_lines(fpath0,line_size=100): #get number of lines of a file with fixed line size
  if not os.path.exists(fpath0): return 0
  file_size=os.path.getsize(fpath0)
  return int(file_size/line_size)

def insert_sorted(str0,fpath0,line_size=100): #insert string in a file to maintain alphabetical order
  cur_line=str0.ljust(line_size-1)+"\n"
  output=False
  if not os.path.exists(fpath0):
    fopen=open(fpath0,"w")
    fopen.write(cur_line)
    fopen.close()
    return output
  #print("now adding to an existing file")
  tmp = tempfile.NamedTemporaryFile(delete=True)
  shutil.copy2(fpath0, tmp.name)
  write_fopen=open(fpath0,"w")
  tmp_fpath=tmp.name
  fopen=open(tmp_fpath)
  added=False
  for li in fopen:
    if li.strip()==str0.strip():
      output=False
    elif str0<li: #if the string to be inserted is smaller than the current line (before it in the sorting order)
      if added==False:
        write_fopen.write(cur_line) #write the string first, then the current line
        write_fopen.write(li)
        added=True
      else: write_fopen.write(li) #if it was already added

    else:
      write_fopen.write(li)
  if added==False: write_fopen.write(cur_line) #if the string is not added yet, then add it at the end of the line
  fopen.close()
  write_fopen.close()
  return output

def inc_count_items(items,fpath): #add items to a text file, indicate their count, and increment each time an item is add it, and move it up the list
  item_count_dict={}
  used_counter=0
  for it0 in items: item_count_dict[it0]=1
  in_fpath=fpath
  tmp = tempfile.NamedTemporaryFile(delete=False)
  tmp_fpath=tmp.name
  if not os.path.exists(in_fpath):
    in_fopen=open(in_fpath,"w")
    for it0 in items:
      line0="%s\t%s\n"%(it0,1)
      in_fopen.write(line0)
    in_fopen.close()
  else:
    in_fopen=open(in_fpath)
    n_lines=0
    for line0 in in_fopen:
      n_lines+=1
      split0=line0.strip().split("\t")
      key0,count_str0=split0
      if key0 in items:
        item_count_dict[key0]=int(count_str0)+1
        used_counter+=1
        if used_counter==len(items): break
    in_fopen.close()
    items_count_list=sorted(list(item_count_dict.items()),key=lambda x:-x[1])
    out_fopen=open(tmp_fpath,"w")
    in_fopen=open(in_fpath)
    for i0,line0 in enumerate(in_fopen):
      applied_items_list=[]
      split0=line0.strip().split("\t")
      key0,count_str0=split0
      line_count0=int(count_str0)
      for item_count1 in items_count_list:
        item1,count1=item_count1
        if count1>=line_count0:
          new_line0="%s\t%s\n"%(item1,count1)
          out_fopen.write(new_line0)
          applied_items_list.append(item1)
      items_count_list=items_count_list[len(applied_items_list):]
      if not key0 in items: out_fopen.write(line0)
    for item_count1 in items_count_list:
      item1,count1=item_count1
      new_line0="%s\t%s\n"%(item1,count1)
      out_fopen.write(new_line0)
    in_fopen.close()
    out_fopen.close()
  if os.path.exists(tmp_fpath):shutil.move(tmp_fpath,in_fpath)  