function $$(el_id){
    return document.getElementById(el_id)
}

function img(src,onload=null,id=""){ //create img object
    new_img=new Image()
    
    if (id!="") new_img.id=id;
    if (onload!=null) new_img.onload=onload
    new_img.src=src;
    return new_img
}

function load_images(img_list,callback_fn=null){ //loading a group of images, adding them to images variable/namespace
    images.loaded_images=[] //we need to have a global variable called "images"
    for (im in img_list){
        cur_img_src=img_list[im]
        cur_img_src_split=cur_img_src.split("/")
        cur_img_id=cur_img_src_split[cur_img_src_split.length-1].split(".")[0]
        console.log(cur_img_id)
        new_img=new Image()
        new_img.src=cur_img_src
        new_img.id=cur_img_id
        images[cur_img_id]=new_img
        new_img.onload=function(){
            console.log(this)
            images.loaded_images.push(cur_img_id)
            if (images.loaded_images.length==img_list.length) callback_fn()
        }
        new_img.onerror=function(){
            console.log("error", this)
            images.loaded_images.push(cur_img_id)
            if (images.loaded_images.length==img_list.length) callback_fn()
        }        
    }
}

function load_sounds(sound_list,callback_fn=null){ //loading a group of sounds, adding them to images variable/namespace
    sounds.loaded_sounds=[] //we need to have a global variable called "sounds"
    for (snd in sound_list){
        cur_snd_src=sound_list[snd]
        cur_snd_src_split=cur_snd_src.split("/")
        cur_snd_id=cur_snd_src_split[cur_snd_src_split.length-1].split(".")[0]
        //console.log(cur_snd_id)
        new_snd=new Audio()
        new_snd.src=cur_snd_src
        new_snd.id=cur_snd_id
        //console.log(new_snd)
        sounds[cur_snd_id]=new_snd
        new_snd.addEventListener('canplaythrough', function() { 
           console.log(this)
            sounds.loaded_sounds.push(cur_snd_id)
            if (sounds.loaded_sounds.length==sound_list.length) callback_fn()
        }, false);
        new_snd.onerror=function(){
            console.log("error", this)
            sounds.loaded_sounds.push(cur_snd_id)
            if (sounds.loaded_sounds.length==sound_list.length) callback_fn()
        }        
    }
}

function aud(src,id="",onload=null,onended=null){ //create audio object
    new_aud=new Audio()
    new_aud.src=src;
    if (id!="") new_aud.id=id;
    if (onload!=null) new_aud.onload=onload
    if (onended!=null) new_aud.onended=onended
    return new_aud
}


function hide_class(class_name){
    all_class_items=document.getElementsByClassName(class_name)        
    for (am in all_class_items) all_class_items[am].hidden=true;        
}
function show_class(class_name){
    all_class_items=document.getElementsByClassName(class_name)        
    for (am in all_class_items) all_class_items[am].hidden=false;        
}
    
function shuffle(a) {
    var j, x, i;
    for (i = a.length - 1; i > 0; i--) {
        j = Math.floor(Math.random() * (i + 1));
        x = a[i];
        a[i] = a[j];
        a[j] = x;
    }
    return a;
}

function set_local_strorage(obj_name,obj_key,obj_val){
  retrieved_obj=localStorage.getItem(obj_name);
  parsed=JSON.parse(retrieved_obj)
  if (parsed==null) parsed={}
  parsed[obj_key]=obj_val
  localStorage.setItem(obj_name, JSON.stringify(parsed));
}


function get_local_strorage(obj_name,obj_key){
  retrieved_obj=localStorage.getItem(obj_name);
  parsed=JSON.parse(retrieved_obj)
  if (parsed==null) parsed={}
  val=parsed[obj_key]
  //parsed[obj_key]=obj_val
  //localStorage.setItem(obj_name, JSON.stringify(parsed));
  return val
}

function create_el_basic(el_tag,el_parent){
    var el0=document.createElement(el_tag)
    el_parent.appendChild(el0)
    return el0
}

function create_el(el_tag,el_parent,el_id,el_name,el_html){
    var el0=document.createElement(el_tag)
    el_parent.appendChild(el0)
    if (el_id!="") el0.id=el_id
    if (el_name!="") el0.name=el_name
    if (el_html!="") el0.innerHTML=el_html
    return el0
}

function post_data(link,obj2upload,callback_fn){
    //we expect both uploaded data and received data to be of json format
    fetch(link,
      {
          method: "POST",
          body: JSON.stringify(obj2upload)
      })
      .then(function(res){ return res.json(); })
      .then(function(data){
        //console.log(data)
        callback_fn(data)
      })    
}

function check_email_str(email_str){
    split=email_str.split("@")
    if (split.length!=2) return false
    domain_split=split[1].split(".")
    if (domain_split.length<2) return false
    return true
}

function show_screen(screen_id){
    $(".screen").hide()
    $("#"+screen_id).show()
    $$(screen_id).hidden=false;
    return $$(screen_id)
}
function gen_options(correct_option,option_pool,n_options=4){
    option_pool_copy=option_pool.slice()
    shuffle(option_pool_copy)
    cur_i=option_pool_copy.indexOf(correct_option)
    option_pool_copy.splice(cur_i, 1);
    cur_options=[correct_option]
    for (var i=0;i<n_options-1;i++) cur_options.push(option_pool_copy[i])
    return cur_options
    
}

function get_1st_random(items){
    shuffle(items)
    return items[0]
}

////add line break to split text across multiple lines, specifying maximum width in characters
function multiline1(txt,max_size){
    words=txt.split(" ")
    new_words=[]  
    offset=0
    for (wd in words){
        cur_word=words[wd]
        offset+=cur_word.length
        if (offset>max_size){
            new_words.push("\n"+cur_word)
            offset=0
        }
        else new_words.push(cur_word)
    }
    out= $.trim(new_words.join(" "))
    return out
    
}



////add line break to split text across multiple lines, specifying maximum width in characters, 
//respecting the original breaks, and also respecting the <br> breaks if any
function multiline(txt,max_size){
    final_segs=[]
    txt=txt.split("\n").join("<br>")
    segs=txt.split("<br>")
    for (const sg of segs){
        words=sg.split(" ")
        new_words=[]  
        offset=0
        for (wd in words){
            cur_word=words[wd]
            offset+=cur_word.length
            if (offset>max_size){
                new_words.push("\n"+cur_word)
                offset=0
            }
            else new_words.push(cur_word)
        }
        out= $.trim(new_words.join(" ")) //need to have jquery
        final_segs.push(out)
        
    }
    final_str=final_segs.join("\n")
    return $.trim(final_str)
    
}

//turn a list of items into a list of lists
function nesting(list1,max_sublist_size){
    sublist_items=[]
    list_of_lists=[]
    for (it in list1){
        cur_item=list1[it]
        sublist_items.push(cur_item)
        if (sublist_items.length==max_sublist_size){
            list_of_lists.push(sublist_items)
            sublist_items=[]
        }
    }    
    if (sublist_items.length>0) list_of_lists.push(sublist_items)
    return list_of_lists
}

function split(txt){
    if (txt=="") return []
    txt=$.trim(txt)
    items=[]
    txt_split=txt.split(" ")
    for (ts in txt_split) items.push($.trim(txt_split[ts]))
    return items
}

function getRandomColor() {
  var letters = '0123456789ABCDEF';
  var color = '#';
  for (var i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

function push(list,item){ //push an item to an array that may have not been defined before
    if (list==undefined || list==null) list=[]
    list.push(item)
    return list
}

function filter_list(list,key,val){ //array of objects- get only items with certain value for a key
    new_list=[]
    for (it in list){
        cur_item=list[it]
        if (cur_item[key]==val) new_list.push(cur_item)
    }
    return new_list
}

function get_vals(class_name){ //get the vals from inputs of a form
    val_dict={}
    elements=document.getElementsByClassName(class_name)
    used_names=[] //to address radio buttons, where inputs have the same names
    for (el in elements){
        cur_el=elements[el]
        el_name=cur_el.name
        el_value=cur_el.value
        if (el_name==null || el_name==undefined) continue
        if (el_value==null || el_value==undefined) continue
        if (used_names.indexOf(el_name)>-1) continue
        
        if (cur_el.type=="radio"){
            used_names.push(el_name)
            var radios = document.getElementsByName(el_name);
            for (rd in radios){
                //check if the radio button is of the same class
                cur_rd=radios[rd]
                if (cur_rd.checked) val_dict[el_name]=cur_rd.value
            }
        }
        else if (cur_el.type=="checkbox") val_dict[el_name]=cur_el.checked
        else val_dict[el_name]=el_value
    }
    return val_dict
}

function listToMatrix(list, elementsPerSubArray) {
    var matrix = [], i, k;

    for (i = 0, k = -1; i < list.length; i++) {
        if (i % elementsPerSubArray === 0) {
            k++;
            matrix[k] = [];
        }

        matrix[k].push(list[i]);
    }

    return matrix;
}  