level_bubble_radius=100
//level_list=[
//    ["lvl1","Alphabet",0.5,0.1,"",{desc:"Alphabet letters names and shapes",unlocked:true,premium:false,color:"Green",image:null}],
//    ["lvl2","Sounds",0.75,0.3,"lvl1",{desc:"Diacritics and letter sounds",unlocked:true,premium:false,color:"Green",image:null}],
//    ["lvl3","Letters\nin Words",0.5,0.3,"lvl1",{desc:"Letters in words",unlocked:true,premium:false,color:"Green",image:null}],
//    ["lvl4","Combine\nLetters",0.5,0.5,"lvl3",{desc:"Combine letters to make words",unlocked:true,premium:false,color:"Green",image:null}],
//    ["lvl5","Keyboard",0.25,0.3,"lvl1",{desc:"Combine letters to make words",unlocked:true,premium:false,color:"Green",image:null}],   
//    ["lvl6","Read Words",0.75,0.5,"lvl2",{desc:"Combine letters to make words",unlocked:true,premium:false,color:"Green",image:null}], 
//    ["lvl7","Write\nWords",0.25,0.5,"lvl5",{desc:"Combine letters to make words",unlocked:true,premium:false,color:"Green",image:null}], 
//    ["lvl8","Vocabulary 1",0.5,0.7,"lvl4,lvl6,lvl7",{desc:"Combine letters to make words",unlocked:true,premium:false,color:"Green",image:null}],   
//    ["lvl9","Vocabulary 2",0.5,0.9,"lvl8",{desc:"Combine letters to make words",unlocked:true,premium:false,color:"Green",image:null}],     
//]

//draw level map
function draw_levels(level_list,level_fn, x0_,y0_,w0_,h0_,completed_ids=[], bubble_radius=100){ //what function to be called when a level is clicked
    //cur_canvas_id="canvas_levels"
    //cur_canvas=$$(cur_canvas_id)
    //show_screen(cur_canvas_id)
    //cur_stage=set_stage(cur_canvas_id,500,window.innerHeight*0.8)
    //cur_stage.removeAllChildren()
    
    //title=draw_text(w/2,10,"Levels")
    
    var level_container = new createjs.Container();
    //cur_stage.addChild(level_container)
    child_parent_list=[]
    xy_dict={}
    parent_dict={}
    all_bubbles=[]
    for (lv in level_list){
        cur_level_obj=level_list[lv]
        node_id=cur_level_obj.id
        node_name=cur_level_obj.name
        parent_id=cur_level_obj.prequisite
        if (cur_level_obj.prequisite=="") prequisites=[]
        else prequisites=cur_level_obj.prequisite.split(",")
        
        //choosing the level bubble color
        cur_color="Blue" //default-open
        if (completed_ids.indexOf(node_id)>-1) cur_color="Green"  //completed       
        for (pr in prequisites){
            if (completed_ids.indexOf(prequisites[pr])==-1) cur_color="Darkgrey" //still locked
        } 
        console.log(prequisites,completed_ids,node_id)
        var x=x0_+w0_*cur_level_obj.x;
        var y=y0_+h0_*cur_level_obj.y;
        //var bub0=draw_bubble(x,y,node_name,null,"blue",bubble_radius,"bold 16px Arial")
        //console.log(completed_ids,node_id)
        node_name_multiline=multiline(node_name,10)
        var bub0=draw_button(x,y,node_name_multiline,null,cur_color,100,40,10,txt_style="bold 18px Arial",txt_color="#FFFFFF")
        bub0.on("click",level_fn)
        bub0.id=node_id
        bub0.name=node_name
        xy_dict[node_id]=[x,y]
        all_bubbles.push(bub0)
        if (parent_id!="") {
            parent_id_split=parent_id.split(",")
            parent_dict[node_id]=parent_id_split
            for (pi in parent_id_split) child_parent_list.push([node_id,parent_id_split[pi]])
        } 
    }    
    for (ch in child_parent_list){
        cur_pair=child_parent_list[ch]
        var [x0,y0]=xy_dict[cur_pair[0]]
        var [x1,y1]=xy_dict[cur_pair[1]]
        line1=draw_line(x0,y0,x1,y1)
        level_container.addChild(line1)
        
    }
    for (b in all_bubbles) level_container.addChild(all_bubbles[b])

//    btn1=draw_button(w-50,30,"Menu",null,"Green",100,60,10)
//    btn1.on("click",draw_menu)    
    
    //cur_stage.addChild(title)
    //cur_stage.update()    
    return level_container
    
}