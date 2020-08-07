from gtts import gTTS
import os
lang="ar"

cur_dir="ar_recordings"
if not os.path.exists(cur_dir): os.mkdir(cur_dir)
fopen=open("arlist.tsv")
for i,a in enumerate(fopen):
	if i==0: continue
	split=a.strip("\n\r").split("\t")
	if len(split)!=2: continue
	fn_, ar_=split
	print(fn_, ar_)
	fn_=fn_.replace(" ","_")
	tts = gTTS(ar_,lang='ar')
	fpath=os.path.join(cur_dir,fn_)+".mp3"
	tts.save(fpath)

	#print(fn_,ar_)
fopen.close()