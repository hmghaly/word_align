import os, sys, shelve, json, random, subprocess, tempfile, socket, time
import base64
import smtplib #email libraries
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from smtplib import SMTP_SSL as SMTP
import hashlib
import datetime
from datetime import date
import uuid



def hash_password(pwd0):
    pwd0=pwd0.encode('utf-8')
    return hashlib.sha256(pwd0).hexdigest()

def send_email(email_to0,email_subject0,email_html0,email_from0="contact@kmatters.com",email_password0="V9EF#rzC;h(J", from_name0="B2WEB Team",server_name0="a2plcpnl0342.prod.iad2.secureserver.net",port0=465):
    server = SMTP(server_name0)
    server.set_debuglevel(False)
    server.login(email_from0, email_password0)
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject0 #"Registration Successful!"
    email_from_full = "%s <%s>"%(from_name0,email_from0)
    msg['From'] = email_from_full
    msg['To'] = email_to0
    msg['Message-ID'] = make_msgid()

    email_txt0=email_html0.replace("<br>","\n")

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(email_txt0, 'plain')
    part2 = MIMEText(email_html0, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    #s = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    server.sendmail(email_from0, email_to0, msg.as_string())
    server.quit()  
    return str(msg)

def today():
    return date.today().isoformat()

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
    #key0=key0.encode("utf-8")
    shelve_open0=shelve.open(shelve_path0)
    shelve_open0[key0]=item_json_info0
    shelve_open0.close()



def lookup_item(item_id0,shelve_path0):
    #item_id0=item_id0.encode("utf-8")
    shelve_open0=shelve.open(shelve_path0)
    found=shelve_open0.get(item_id0,"{}")
    found_dict=json.loads(found)
    shelve_open0.close()
    return found_dict


def append2item_list(item_id0,shelve_path0,val2append0):
    #item_id0=item_id0.encode("utf-8")
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
    
    result["time"]=time.time()
    #stdin_str=sys.stdin.read()
    try:
        stdin_str=sys.stdin.read()
        input_dict=json.loads(stdin_str)
        #form =  cgi.FieldStorage() 
        cur_base64_data = input_dict['data']
        for key0 in input_dict.keys():
            if key0=="data": continue
            result[key0]=input_dict.get(key0)
        fname = input_dict.get('fname')
        dir_path = input_dict.get('dir_path')
        if dir_path==None: dir_path="/tmp"
        try: 
            if not os.path.exists(dir_path): os.makedirs(dir_path)
        except: dir_path="/tmp"
        if fname==None: fname=gen_hex(4)
        full_wav_fpath=os.path.join(dir_path,fname+".wav")
        write_base64(cur_base64_data,full_wav_fpath)
        full_json_fpath=os.path.join(dir_path,fname+".json")
        full_json_fopen=open(full_json_fpath,"w")
        json.dump(result,full_json_fopen)
        full_json_fopen.close()
        result["wav_fpath"]=full_wav_fpath
        if result.get("mp3",False) or result.get("mp3","").lower()=="true":
            mp3_path=full_wav_fpath.replace(".wav",".mp3")
            proc=subprocess.Popen("lame -V2 %s %s"%(full_wav_fpath,mp3_path),shell=True)
            proc.wait()
            if os.path.exists(mp3_path): result["mp3_fpath"]=mp3_path
            else: result["mp3_fpath"]=""
            
        result["success"]=True
    except Exception as e:
        message=str(e)
        result["success"]=False
        result["message"]=str(e)    
    return result

# def save_audio():
#     result={}
#     result["message"]=""
#     result["success"]=False
#     try:
#         form = cgi.FieldStorage() 
#         fileitem = form['data']
#         for key0 in form.keys():
#             if key0=="data": continue
#             result[key0]=form.getvalue(key0)
#         fname = form.getvalue('fname')
#         dir_path = form.getvalue('dir_path')
#         if dir_path==None: dir_path="/tmp"
#         try: 
#             if not os.path.exists(dir_path): os.makedirs(dir_path)
#         except: dir_path="/tmp"
#         if fname==None: fname=gen_hex(4)
#         full_wav_fpath=os.path.join(dir_path,fname+".wav")
#         out=open(full_wav_fpath,'wb')
#         out.write(fileitem.file.read())
#         out.close()    
#         result["wav_fpath"]=full_wav_fpath
#         if result.get("mp3","").lower()=="true":
#             mp3_path=full_wav_fpath.replace(".wav",".mp3")
#             proc=subprocess.Popen("lame -V2 %s %s"%(full_wav_fpath,mp3_path),shell=True)
#             proc.wait()
#             if os.path.exists(mp3_path): result["mp3_fpath"]=mp3_path
#             else: result["mp3_fpath"]=""
            
#         result["success"]=True
#     except Exception as e:
#         message=str(e)
#         result["message"]=str(e)    
#     return result    

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

def get_wsgi_qs(environ):
    qs=environ["QUERY_STRING"]
    qs_dict0={}
    split_qs=qs.split("&")
    for item0 in split_qs:
        eq_split=item0.split("=")
        if len(eq_split)!=2: continue
        key0,val0=eq_split
        qs_dict0[key0]=val0
    return qs_dict0

def get_wsgi_posted_data(environ):
  posted_data=""
  posted_data_dict={}
  if environ['REQUEST_METHOD'] == 'POST': 
    posted_data=environ['wsgi.input'].read().decode("utf-8")
    posted_data_dict=json.loads(posted_data)
  return posted_data_dict

def get_wsgi_cookie(environ):
  cookie_str=environ.get("HTTP_COOKIE","")
  cookie_split=cookie_str.split(";")
  cookie_dict={}
  for sp in cookie_split:
      key_val=sp.split("=")
      if len(key_val)!=2: continue
      key,val=key_val
      key,val=key.strip(),val.strip()
      cookie_dict[key]=val
  return cookie_dict

def generate_uuid():
    return str(uuid.uuid4())

def read_file(fpath0):
    fopen0=open(fpath0)
    content0=fopen0.read()
    fopen0.close()
    return content0

def split_list(l, n): #split a list into equally sized sublists
    grp_size=math.ceil(len(l)/n)
    for i0 in range(n): yield l[i0*grp_size:(i0+1)*grp_size]

def create_selection_options(list_vals_labels,selected0=None): # create selection drop down from a list of labels and vals
    cur_dropdown_content=''
    for val0,label0 in list_vals_labels:
        cur_op_tag='<option value="%s">%s</option>'%(val0,label0)
        if val0==selected0: cur_op_tag='<option value="%s" selected>%s</option>'%(val0,label0)
        cur_dropdown_content+=cur_op_tag
    return cur_dropdown_content 

def create_time_str(time_tuple):
    time_str="%s/%s/%s - %s:%s:%s"%(time_tuple[0],time_tuple[1],time_tuple[2],time_tuple[3],time_tuple[4],time_tuple[5])
    return time_str


def log_something(environ0,log_fpath0,log_content_dict0={}):
    user_ip=environ0.get("REMOTE_ADDR","IP")
    cur_log_dict=dict(log_content_dict0)
    cur_log_dict["IP"]=user_ip
    now = datetime.datetime.now()
    cur_log_dict["time"]=(now.year, now.month, now.day, now.hour, now.minute, now.second)
    log_dir0,log_fname0=os.path.split(log_fpath0)
    if not os.path.exists(log_dir0): os.makedirs(log_dir0)
    log_fopen0=open(log_fpath0,"a")
    log_fopen0.write(json.dumps(cur_log_dict)+"\n")
    log_fopen0.close()
    return True

# def hash_password(pwd0):
#     pwd0=pwd0.encode('utf-8')
#     return hashlib.sha256(pwd0).hexdigest()

def get_time_tuple():
    now = datetime.datetime.now()
    return (now.year, now.month, now.day, now.hour, now.minute, now.second) 


#save uploaded base64 string from javascript to binary form
def write_base64(base64_uploaded_str0,out_fpath0):
  split_str=base64_uploaded_str0.split(";base64,")
  file_data=split_str[-1]
  with open(out_fpath0, "wb") as fh:
    binary_content=base64.b64decode(file_data)
    fh.write(binary_content)

# file_type=".wav"
# file_type=".mp3"
# proj_name="alphabet"
# user_name="user"
# dir_path=os.path.join("projects",proj_name,user_name)

# zip_fname=proj_name+".zip"
# zipf = zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED)
# zipdir(dir_path, zipf,file_type)
# zipf.close()