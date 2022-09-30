import os, sys, shelve, json, random, subprocess, tempfile, socket

def gen_hex(N=10):
    chars = '0123456789abcdef'
    return "".join(random.sample(chars,N))

def add_item(item_json_info0,shelve_path0,overwrite=False,code_size=4,max_iters=200):
    shelve_open0=shelve.open(shelve_path0)
    if overwrite:
        cur_code=gen_hex(code_size)
        shelve_open0[cur_code]=item_json_info0
        shelve_open0.close()
        return cur_code

    cur_code="" #gen_hex(code_size)
    success=False
    for _ in range(max_iters):
        cur_code=gen_hex(code_size)
        found=shelve_open0.get(cur_code)
        if found==None:
            shelve_open0[cur_code]=item_json_info0
            success=True
            break
    shelve_open0.close()
    return cur_code

def add_item_simple(key0,shelve_path0,item_json_info0):
    key0=key0.encode("utf-8")
    shelve_open0=shelve.open(shelve_path0)
    shelve_open0[key0]=item_json_info0
    shelve_open0.close()



def lookup_item(item_id0,shelve_path0):
    item_id0=item_id0.encode("utf-8")
    shelve_open0=shelve.open(shelve_path0)
    found=shelve_open0.get(item_id0,"{}")
    found_dict=json.loads(found)
    shelve_open0.close()
    return found_dict


def append2item_list(item_id0,shelve_path0,val2append0):
    item_id0=item_id0.encode("utf-8")
    shelve_open0=shelve.open(shelve_path0)
    found=shelve_open0.get(item_id0,"[]")
    found_list=json.loads(found)
    if not val2append0 in found_list: 
        new_list=found_list+[val2append0]
        shelve_open0[item_id0]=json.dumps(new_list)
    shelve_open0.close()
    return new_list


def update_item(item_id0,shelve_path0,update_dict0={}):
    shelve_open0=shelve.open(shelve_path0)
    found=shelve_open0.get(item_id0,"{}")
    found_dict=json.loads(found)
    for a,b in update_dict0.items():
        found_dict[a]=b
    shelve_open0[item_id0]=json.dumps(found_dict)
    shelve_open0.close()
    return found

def run_command(command_str0):
    proc = subprocess.Popen(command_str0,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = proc.stdout.read()
    # proc.wait()
    # lines=[]
    # for op in proc.stdout: lines.append(op)
    #output = proc.stdout.read()
    return str(output)#output#str(proc)#output#.strip()

def read_json(json_fpath0):
    fopen0=open(json_fpath0)
    json_dict=json.load(fopen0)
    fopen0.close()
    return json_dict


def send2socket(input0,HOST, PORT):
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10.0)
    s.connect((HOST, PORT))
    #s.sendall(input_dict_json.encode("utf-8"))
    s.sendall(input0.encode("utf-8"))
    received_data = s.recv(1024)
    # output_dict["received_data"]=received_data
    # output_dict["success"]=True
    # output_dict["message"]="success"
    s.close()
    return received_data    
# def create_tmp_json(json_data0):
#     tmp = tempfile.NamedTemporaryFile(delete=False)
#     try:
#         #print(tmp.name)
#         tmp.write(json_data0.encode("utf-8"))
#     finally:
#         tmp.close()
#         #os.unlink(tmp.name) 
#     return tmp.name   


def create_tmp_json(json_data0):
    tmp_fname=gen_hex()
    tmp_dir="tmp"
    if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
    tmp_fpath=os.path.join(tmp_dir,tmp_fname)
    tmp_fopen=open(tmp_fpath,"w")
    tmp_fopen.write(json_data0)
    tmp_fopen.close()

    # tmp = tempfile.NamedTemporaryFile(delete=False)
    # try:
    #     #print(tmp.name)
    #     tmp.write(json_data0.encode("utf-8"))
    # finally:
    #     tmp.close()
        #os.unlink(tmp.name) 
    return tmp_fpath

def save_audio():
    result={}
    result["message"]=""
    result["success"]=False
    try:
        form = cgi.FieldStorage() 
        fileitem = form['data']
        for key0 in form.keys():
            if key0=="data": continue
            result[key0]=form.getvalue(key0)
        fname = form.getvalue('fname')
        dir_path = form.getvalue('dir_path')
        if dir_path==None: dir_path="/tmp"
        try: 
            if not os.path.exists(dir_path): os.makedirs(dir_path)
        except: dir_path="/tmp"
        if fname==None: fname=gen_hex(4)
        full_wav_fpath=os.path.join(dir_path,fname+".wav")
        out=open(full_wav_fpath,'wb')
        out.write(fileitem.file.read())
        out.close()    
        result["wav_fpath"]=full_wav_fpath
        if result.get("mp3","").lower()=="true":
            mp3_path=full_wav_fpath.replace(".wav",".mp3")
            proc=subprocess.Popen("lame -V2 %s %s"%(full_wav_fpath,mp3_path),shell=True)
            proc.wait()
            if os.path.exists(mp3_path): result["mp3_fpath"]=mp3_path
            else: result["mp3_fpath"]=""
            
        result["success"]=True
    except Exception,e:
        message=str(e)
        result["message"]=str(e)    
    return result    

import zipfile
def zipdir(path, zip_fpath,file_type=""):
    # ziph is zipfile handle
    ziph = zipfile.ZipFile(zip_fpath, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for fname in files:
            if not fname.endswith(file_type): continue
            ziph.write(os.path.join(root, fname))
    ziph.close()


def get_qs():
    qs_dict0={}
    qs=os.environ.get("QUERY_STRING","")
    split_qs=qs.split("&")
    for item0 in split_qs:
        eq_split=item0.split("=")
        if len(eq_split)!=2: continue
        key0,val0=eq_split
        qs_dict0[key0]=val0
    return qs_dict0


# file_type=".wav"
# file_type=".mp3"
# proj_name="alphabet"
# user_name="user"
# dir_path=os.path.join("projects",proj_name,user_name)

# zip_fname=proj_name+".zip"
# zipf = zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED)
# zipdir(dir_path, zipf,file_type)
# zipf.close()