import socket, os, subprocess, urllib

tika_fname="tika-app-1.11.jar"
tika_url= "http://archive.apache.org/dist/tika/tika-app-1.11.jar"
if not os.path.exists(tika_fname):
    print("apache tika does not exist, downloading from: %s"%tika_url)
    try:
        urllib.urlretrieve ("http://archive.apache.org/dist/tika/tika-app-1.11.jar", "tika-app-1.11.jar")
        print("Tika downloaded successfully")
    except Exception, e:
        print(e)
        print("failed to download tika, please download manually from %s"%tika_url)
    
        
        
host_name=socket.gethostname()
port_number=12345
shell_command='java -jar %s -h --encoding=utf-8  --server --port %s'%(tika_fname,port_number)
try:
    proc=subprocess.Popen(shell_command,shell=True)
except Exception,e:
    print(e)

def tika(ourfile,port=port_number,host=host_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(25.0)
    s.connect((host,port))
    f = open(ourfile, 'rb')
    while True:
        chunk = f.read(65536)
        if not chunk:
            break
        s.sendall(chunk)
    s.shutdown(socket.SHUT_WR)
    final_content=''
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        final_content+=chunk
    return final_content

if __name__=="__main__":
    fname=r'test.docx'
    out=tika(fname)
    print(out)
