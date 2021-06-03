function draw_keyboard(layout,x0,y0,w0,h0,btn_fn,key_size=15){
    console.log(layout)
    spacing=3
    n_row_keys=11
    key_size=(w0-(n_row_keys-1)*spacing)/n_row_keys
    x0_=x0
    y0_=y0
    x0_+=key_size*0.5;
    y0_+=key_size*0.5;
    screen_h=60; //screen where the typed letters appear
    btn_list=[]
    kb_container= new createjs.Container();
    input_area_x=x0+w0/2
    input_area_y=y0-screen_h/2-spacing
    input_area_bg=draw_button(input_area_x,input_area_y,text="","","white",w0,screen_h,5)
    input_area_txt=draw_text(input_area_x,input_area_y,"",txt_style="bold 24px Comic",txt_color="#000")
    kb_container.addChild(input_area_bg,input_area_txt)
    for (var j=0;j<3;j++){
        for (var i=0;i<n_row_keys;i++){
            console.log(i,j,x0_,y0_)
            key_id=""+j+"-"+i
            corr=layout[key_id]
            console.log(corr)
            //text1=draw_text(x0_,y0_,"1")
            
            btn2=draw_button(x0_,y0_,corr[0],"","purple",key_size,key_size,5)
            btn2.name=corr[0]
            btn2.shift=false
            btn2.char_list=corr //the button with shift
            kb_container.addChild(btn2)
            btn_list.push(btn2)
            btn2.on("click",function(obj){
                text=input_area_txt.text
                if (obj.currentTarget.name=="back") text = text.substring(0, text.length - 1);
                else text+=obj.currentTarget.name
                //text+=obj.currentTarget.name
                input_area_txt.text=text      
                kb_container.text=text
                btn_fn(kb_container)
            })
            //kb_container.addChild(text1)
            x0_+= key_size+spacing

        }
        y0_+= key_size+spacing
        x0_=x0+key_size*0.5;        
    }
    
    x0_=(2*key_size+spacing)/2
    shift_btn=draw_button(x0_,y0_,text="Shift","","red",key_size*2,key_size,5)
    shift_btn.shift=false;
    shift_btn.on("click",function(obj){
        if (shift_btn.shift==false){
            shift_btn.shift=true;
            for (bt in btn_list){
                cur_btn=btn_list[bt]
                cur_btn.name=cur_btn.char_list[1]
                cur_btn.children[1].text=cur_btn.name
                console.log(cur_btn)
            }
        }
        else {
            shift_btn.shift=false;
            for (bt in btn_list){
                cur_btn=btn_list[bt]
                cur_btn.name=cur_btn.char_list[0]
                cur_btn.children[1].text=cur_btn.name
                console.log(cur_btn)
            }            
        }
        stage.update()
//        console.log(obj)
//        console.log(btn_list)
    })
    x0_=w0/2
    space_btn=draw_button(x0_,y0_,text="Space","","purple",key_size*7,key_size,5)
    space_btn.name=" "
    space_btn.on("click",function(){
        input_area_txt.text+=" "      
        kb_container.text=input_area_txt
        btn_fn(kb_container)        
    })
    x0_=(10*key_size+9.5*spacing)
    back_space_btn=draw_button(x0_,y0_,text="Back","","red",key_size*2,key_size,5)
    back_space_btn.name="back"
    back_space_btn.on("click",function(){
            text=input_area_txt.text
            text = text.substring(0, text.length - 1)
            input_area_txt.text=text      
            kb_container.text=text
            btn_fn(kb_container)
        
    })
    
    kb_container.addChild(shift_btn,space_btn,back_space_btn)
    

    
    return kb_container
}


function save_progress(){
    progress={}
    progress["user"]=user
    progress["quiz"]=quiz
    set_local_strorage(storage_name,"progress",progress)
}

function load_progress(){
    progress=get_local_strorage(storage_name,"progress")
    return progress
}

//draw the multiple choice question, with question elements: prompt, item, and options
function deploy_mcq1(q_prompt,q_item,q_options,check_fn,layout=0){ 
    if (layout==0) return deploy_q_layout0(q_prompt,q_item,q_options,check_fn)
}

//we should input the top y and left x and the width and height of the question space
function deploy_q_layout0(q_prompt,q_item,q_options,check_fn){
    q_container=new createjs.Container();
    q_prompt_ml=multiline(q_prompt,20)
    q_item_ml=multiline(q_item,10)
    q_prompt_h=40
    base_y=0.2*h
    q_prompt_y=base_y-0.5*q_prompt_h
    var prompt_but=draw_button(w/2,q_prompt_y,text=q_prompt_ml,"","darkorange",w,q_prompt_h,0)
    q_item_y=base_y+0.5*q_prompt_h
    //q_item_y=
    var item_but=draw_button(w/2,q_item_y,text=q_item_ml,"","lightblue",w,q_prompt_h,0)
    shuffle(q_options)
    y0=0.4*h
    //y0=q_item_y+item_text_h+50
    
    for (op in q_options){
        op_str=q_options[op]
        var color=getRandomColor()
        var color="violet"
        op_str_ml=multiline(op_str,10) //multiline string
        var op_but=draw_button(w/2,y0,text=op_str_ml,"",color,200,40,10)
        op_but.name=op_str
        op_but.on("click", check_fn)
        q_container.addChild(op_but)
        y0+=50;
        
    }
    q_container.addChild(prompt_but,item_but)  
    return q_container
}

//This is the main function we will use for MCQ
function deploy_q_space_single(q_obj,q_x0,q_y0,q_w0,q_h0,check_fn,layout=1){
    q_container=new createjs.Container();
    //q_prompt="this is a question prompt, let's use it"
    q_prompt=q_obj.prompt
    base_x=q_x0
    base_y=q_y0
    
    q_prompt_ml=multiline(q_prompt,20)
    q_prompt_h=0.15*q_h0
    q_prompt_x=base_x+q_w0/2
    q_prompt_y=base_y+q_prompt_h/2
    base_y+=q_prompt_h
    var prompt_but=draw_button(q_prompt_x,q_prompt_y,text=q_prompt_ml,"","darkorange",q_w0,q_prompt_h,0)

    
    //prompt
    
    //item
    q_item="a book"
    
    q_item=q_obj.item
    q_item_ml=multiline(q_item,20)
    q_item_h=0.1*q_h0
    q_item_x=base_x+q_w0/2
    q_item_y=base_y+q_item_h/2
    base_y+=q_item_h
    var item_but=draw_button(q_item_x,q_item_y,text=q_item_ml,"","lightblue",q_w0,q_item_h,0)
    //var item_but=draw_button(w/2,q_item_y,text=q_item_ml,"","lightblue",w,q_prompt_h,0)
    
    //answer
    q_answer="answer"
    q_answer_ml=multiline(q_answer,10)
    q_answer_h=0.1*q_h0
    q_answer_x=base_x+q_w0/2
    q_answer_y=base_y+q_answer_h/2
    base_y+=q_answer_h
    var answer_but=draw_button(q_answer_x,q_answer_y,text=q_answer_ml,"","lightgrey",q_w0,q_answer_h,0)
    answer_but.name="answer_space"
    answer_but.alpha=0

    
    //options
    //q_options=["ki","t","aa","b"]
    q_options=shuffle(q_obj.options)
    bottom_y=q_y0+q_h0
    remaining_y=bottom_y-base_y
    y_offset=remaining_y/(q_options.length+1)
    //alert([remaining_y,y_offset])
    //y_offset=50
    //
//    rc=draw_rect(q_w0/2,base_y+remaining_y/2,q_w0,remaining_y,"black",rect_r=0)
//    q_container.addChild(rc)
    
    base_y+=y_offset
    
    if (layout==1) options_area_container=options_layout1(base_y,bottom_y,q_w0,q_options,check_fn)
    if (layout==2) options_area_container=options_layout2(base_y,bottom_y,q_w0,q_options,check_fn)
    
//    options_area_container=new createjs.Container();
//    
//    for (op in q_options){
//        if (op_obj.label!=null){
//            op_obj=q_options[op]
//            op_str=op_obj.label
//        } 
//        else {
//            op_str=q_options[op]
//            op_obj.id=op_str
//        } 
//        
//        var color=getRandomColor()
//        var color="violet"
//        op_str_ml=multiline(op_str,20) //multiline string
//        var op_but=draw_button(q_w0/2,base_y,text=op_str_ml,"",color,200,40,10)
//        op_but.name=op_str
//        op_but.id=op_obj.id
//        op_but.on("click", check_fn)
//        options_area_container.addChild(op_but)
//        base_y+=y_offset;
//        
//    }
      
    //message
    
    q_container.addChild(options_area_container)
    q_container.addChild(prompt_but,item_but,answer_but)  
    //q_container.addChild(prompt_but)  
    return q_container
}
//we will also need this, and other layouts
function options_layout1(base_y,bottom_y,q_w0,q_options,check_fn){
    options_area_container=new createjs.Container();
    y_offset=(bottom_y-base_y)/(q_options.length+1)
    colors=["blue","purple","violet","orange"]
    colors=shuffle(colors)
    for (op in q_options){
        if (op_obj.label!=null){
            op_obj=q_options[op]
            op_str=op_obj.label
        } 
        else {
            op_str=q_options[op]
            op_obj.id=op_str
        } 
        
        var color=getRandomColor()
        var color="violet"
        
        var color=colors[op]
        op_str_ml=multiline(op_str,15) //multiline string
        var op_but=draw_button(q_w0/2,base_y,text=op_str_ml,"",color,200,40,10)
        op_but.name=op_str
        op_but.id=op_obj.id
        op_but.on("click", check_fn)
        options_area_container.addChild(op_but)
        base_y+=y_offset;
        
    }
    return options_area_container
}

function options_layout2(base_y,bottom_y,q_w0,q_options,check_fn){
    options_area_container=new createjs.Container();
    y_span=bottom_y-base_y
    y_offset=(bottom_y-base_y)/(q_options.length+1)
    colors=["blue","purple","violet","orange"]
    colors=shuffle(colors)
    xy_list=[[w/4,base_y+y_span/4],
            [w/4,base_y+3*y_span/4],
            [3*w/4,base_y+y_span/4],
            [3*w/4,base_y+3*y_span/4]]

    for (op in q_options){
        if (op_obj.label!=null){
            op_obj=q_options[op]
            op_str=op_obj.label
        } 
        else {
            op_str=q_options[op]
            op_obj.id=op_str
        } 
        
        var color=getRandomColor()
        var color="violet"
        var [x_,y_]=xy_list[op]
        
        var color=colors[op]
        op_str_ml=multiline(op_str,15) //multiline string
        var op_but=draw_button(x_,y_,text=op_str_ml,"",color,q_w0/2,y_span/2,0)
        op_but.name=op_str
        op_but.id=op_obj.id
        op_but.on("click", check_fn)
        options_area_container.addChild(op_but)
        base_y+=y_offset;
        
    }
    return options_area_container
}


function deploy_q_space_multi(q_obj,q_x0,q_y0,q_w0,q_h0,check_fn){
    
    q_container=new createjs.Container();
    //q_prompt="this is a question prompt, let's use it"
    q_prompt=q_obj.prompt
    base_x=q_x0
    base_y=q_y0
    
    q_prompt_ml=multiline(q_prompt,20)
    q_prompt_h=0.2*q_h0
    q_prompt_x=base_x+q_w0/2
    q_prompt_y=base_y+q_prompt_h/2
    base_y+=q_prompt_h
    var prompt_but=draw_button(q_prompt_x,q_prompt_y,text=q_prompt_ml,"","darkorange",q_w0,q_prompt_h,0)

    
    //prompt
    
    //item
    //q_item="a book"
    q_item=q_obj.item
    q_item_ml=multiline(q_item,10)
    q_item_h=0.1*q_h0
    q_item_x=base_x+q_w0/2
    q_item_y=base_y+q_item_h/2
    base_y+=q_item_h
    var item_but=draw_button(q_item_x,q_item_y,text=q_item_ml,"","lightblue",q_w0,q_item_h,0)
    //var item_but=draw_button(w/2,q_item_y,text=q_item_ml,"","lightblue",w,q_prompt_h,0)
    
    //answer
    //q_answer="كتاب"
    //q_answer_ml=multiline(q_answer,10)
    q_answer=""
    q_answer_h=0.15*q_h0
    q_answer_x=base_x+q_w0/2
    q_answer_y=base_y+q_answer_h/2
    base_y+=q_answer_h
    var answer_but=draw_button(q_answer_x,q_answer_y,text=q_answer,"","lightgrey",q_w0,q_answer_h,0)
    answer_but.name="answer_space"
    answer_but.alpha=0

    
    //options
    //q_options=["ki","t","aa","b","la","mi"]
    q_options=q_obj.options
    nested_options=nesting(q_options,4)
    
    bottom_y=q_y0+q_h0
    remaining_y=bottom_y-base_y
    y_offset=remaining_y/(nested_options.length+1)
    base_y+=y_offset

    for (sl in nested_options){
        sublist=nested_options[sl]
        x_offset=q_w0/(sublist.length+1)
        base_x=x_offset
        for (ri in sublist){
            row_item=sublist[ri]
            var op_but=draw_button(base_x,base_y,text=row_item,"","red",40,40,10)
            op_but.name=row_item
            op_but.on("click", check_fn)
            q_container.addChild(op_but)
            base_x+=x_offset
        }

        base_y+=y_offset;
        
    }    
    
    //message
    

    q_container.addChild(prompt_but,item_but,answer_but)  
    //q_container.addChild(prompt_but)  
    return q_container
}

function deploy_q_multi(){
    q_obj=quiz.questions[quiz.i]
    question.correct=q_obj.correct
    
    clean()
    cur_nav=draw_menu_nav()
    cur_nav.name="menu_nav"
    gh_h=40 //game header hight
    cur_gh=draw_game_header(0,cur_nav.upper_y,w,gh_h)
    cur_q_y0=cur_nav.upper_y+gh_h
    cur_q_h0=cur_nav.lower_y-cur_q_y0
    cur_q_space=deploy_q_space_multi(q_obj,0,cur_q_y0,w,cur_q_h0,check_answer_multi)
    //cur_q_space=deploy_q_space_single({},0,cur_q_y0,w,cur_q_h0,check_multi_answer)
    
    stage.addChild(cur_nav, gh_container,cur_q_space)
}

function deploy_q(){
    q_obj=quiz.questions[quiz.i]
    question.correct=q_obj.correct
    question.answers=[]
    audio_src="audio/game/alphabet/"+q_obj.id+".mp3"
    question.audio=new Audio(audio_src)
    
    clean()
    cur_nav=draw_menu_nav()
    cur_nav.name="menu_nav"
    gh_h=40 //game header hight
    cur_gh=draw_game_header(0,cur_nav.upper_y,w,gh_h)
    cur_q_y0=cur_nav.upper_y+gh_h
    cur_q_h0=cur_nav.lower_y-cur_q_y0
    //cur_q_space=deploy_q_space_multi({},0,cur_q_y0,w,cur_q_h0,check_multi_answer)
    cur_q_space=deploy_q_space_single(q_obj,0,cur_q_y0,w,cur_q_h0,check_answer)
    
    stage.addChild(cur_nav, gh_container,cur_q_space)
}


function draw_game_header(gh_x0,gh_y0,gh_width,gh_height,remaining_time=20,callback_fn=function(){}){
    console.log("drawing header")
    gh_container=new createjs.Container();
    mid_gh_y=gh_y0+0.5*gh_height
    gh_rect_bg=draw_rect(gh_x0+0.5*gh_width,mid_gh_y,gh_width,gh_height,"LightBlue")
    gh_rect_bg.name="game_header_bg"
    //gh_rect_bg.alpha=0
    
    x_margin=20
    score_bmp=draw_bitmap(gh_x0+x_margin,mid_gh_y,images.coin,max_height=25,max_width=25)
    score_bmp.name="score_icon"
    score_w=score_bmp._getBounds().width
    score_val=user.score
    if (score_val==null) score_val=0
    score_val=""+score_val
    score_x=score_bmp.x+0.5*score_w+3
    score_txt=draw_text(score_x,mid_gh_y,score_val,txt_style="bold 24px Arial",txt_color="#F0A")
    score_txt.textAlign = "left";
    score_txt.name="score_txt"
    
    //remaining_time=20
    cur_timer=add_timer(remaining_time,w/3,gh_y0+gh_height/2,callback_fn,cur_txt_style="bold 24px Arial",cur_txt_color="#F0A")
    
    accuracy_txt=draw_text(2*w/3,gh_y0+gh_height/2,"100%",txt_style="bold 24px Arial",txt_color="#F0A")
    accuracy_txt.name="accuracy_txt"
    
    
//    lvl_name_str=""
//    if (quiz.name!=null) lvl_name_str=quiz.name
//    
//    progress_str=""
//    if (quiz.i!=null){
//        cur_progress_i=quiz.i+1
//        progress_str=""+cur_progress_i+"/"+quiz.n
//    } 
//    
//    lvl_name_txt=draw_text(gh_x0+0.5*gh_width,gh_y0+0.25*gh_height,lvl_name_str,txt_style="bold 12px Arial",txt_color="#FFFFFF")
//    progress_txt=draw_text(gh_x0+0.5*gh_width,gh_y0+0.75*gh_height,progress_str,txt_style="bold 12px Arial",txt_color="#FFFFFF")
    
//    menu_bmp=draw_bitmap(w-x_margin,mid_gh_y,images.heart,max_height=25,max_width=25)
//    menu_bmp.name="menu_icon"
//    menu_w=menu_bmp._getBounds().width
//    menu_x=menu_bmp.x-menu_w
//    menu_txt=draw_text(menu_x,mid_gh_y,"Menu",txt_style="bold 24px Arial",txt_color="#FFFFFF")
//    menu_txt.name="menu_txt"
//    menu_container=new createjs.Container();
//    menu_container.addChild(menu_bmp,menu_txt)
    
    menu_bubble=draw_bubble_img(w-x_margin,mid_gh_y,images.menu,color="green",txt="Menu",txt_style="bold 12px Arial",txt_color="#F0A",radius=15,max_height=25,max_width=25)
    menu_bubble.on("click",go2menu)
    
    
//    lives_bmp=draw_bitmap(w-x_margin,mid_gh_y,images.heart,max_height=25,max_width=25)
//    lives_bmp.name="lives_icon"
//    lives_w=lives_bmp._getBounds().width
//    lives_val=user.lives
//    if (lives_val==null) lives_val=3
//    lives_val=""+lives_val
//    lives_x=lives_bmp.x-lives_w
//    lives_txt=draw_text(lives_x,mid_gh_y,lives_val,txt_style="bold 24px Arial",txt_color="#FFFFFF")
//    lives_txt.name="lives_txt"

    
    //gh_container.addChild(gh_rect_bg,score_bmp,score_txt,lives_bmp,lives_txt,lvl_name_txt,progress_txt)
    gh_container.addChild(gh_rect_bg,score_bmp,score_txt,cur_timer,accuracy_txt,menu_bubble)
    return gh_container
    
}


//function draw_game_header_old(gh_x0,gh_y0,gh_width,gh_height){
//    console.log("drawing header")
//    gh_container=new createjs.Container();
//    mid_gh_y=gh_y0+0.5*gh_height
//    gh_rect_bg=draw_rect(gh_x0+0.5*gh_width,mid_gh_y,gh_width,gh_height,"green")
//    gh_rect_bg.name="game_header_bg"
//    gh_rect_bg.alpha=0
//    
//    x_margin=20
//    score_bmp=draw_bitmap(gh_x0+x_margin,mid_gh_y,images.coin,max_height=25,max_width=25)
//    score_bmp.name="score_icon"
//    score_w=score_bmp._getBounds().width
//    score_val=user.score
//    if (score_val==null) score_val=0
//    score_val=""+score_val
//    score_x=score_bmp.x+0.5*score_w+3
//    score_txt=draw_text(score_x,mid_gh_y,score_val,txt_style="bold 24px Arial",txt_color="#FFFFFF")
//    score_txt.textAlign = "left";
//    score_txt.name="score_txt"
//    
//    lvl_name_str=""
//    if (quiz.name!=null) lvl_name_str=quiz.name
//    
//    progress_str=""
//    if (quiz.i!=null){
//        cur_progress_i=quiz.i+1
//        progress_str=""+cur_progress_i+"/"+quiz.n
//    } 
//    
//    lvl_name_txt=draw_text(gh_x0+0.5*gh_width,gh_y0+0.25*gh_height,lvl_name_str,txt_style="bold 12px Arial",txt_color="#FFFFFF")
//    progress_txt=draw_text(gh_x0+0.5*gh_width,gh_y0+0.75*gh_height,progress_str,txt_style="bold 12px Arial",txt_color="#FFFFFF")
//    
//    
//    lives_bmp=draw_bitmap(w-x_margin,mid_gh_y,images.heart,max_height=25,max_width=25)
//    lives_bmp.name="lives_icon"
//    lives_w=lives_bmp._getBounds().width
//    lives_val=user.lives
//    if (lives_val==null) lives_val=3
//    lives_val=""+lives_val
//    lives_x=lives_bmp.x-lives_w
//    lives_txt=draw_text(lives_x,mid_gh_y,lives_val,txt_style="bold 24px Arial",txt_color="#FFFFFF")
//    lives_txt.name="lives_txt"
//
//    
//    gh_container.addChild(gh_rect_bg,score_bmp,score_txt,lives_bmp,lives_txt,lvl_name_txt,progress_txt)
//    return gh_container
//    
//}

function check_answer(evt){
    trg=evt.currentTarget
    console.log(trg.name)
    trg.removeAllEventListeners()
    //click_x=evt
//    if (question.collected==null) question.collected=[]
//    expected_answer=question.correct[question.collected.length]
    //trg.on("click",function(){})
    answer_space=get_child(stage,"answer_space")
    
    if (trg.name==question.correct) {
        question.audio.play()
        quiz.i+=1
        if (user.score==null) user.score=0 //updating score
        user.score+=1    
        success_msg_txt="Correct!"
        trg.children[0].graphics._fill.style="green"
        add_coin(trg,function(){})
        if (quiz.i%10==0){
            user.lives+=1
            add_life(trg,function(){})
            save_progress()
            success_msg_txt+="\nGame Saved"

            
        } 
        
        
//        createjs.Tween.get(coin_bitmap).to({guide:{ path:[trg.x,trg.y, trg.x,score_icon.y,score_icon.x,score_icon.y, score_icon.x,trg.y,trg.x,trg.y] }},1000);
        
        //coin_bitmap=draw_bitmap()
        //if (quiz.i>=quiz.n) success_msg_txt+="\nLevel Completed!"
        
        animated_msg(success_msg_txt,answer_space.x,answer_space.y,function(){
            if (quiz.i>=quiz.n) alert("Level Complete!")
            else deploy_q()             
        })
    }
    else {
            trg.children[0].graphics._fill.style="red"
            shake_horizontal(trg,100)
            wrong_answer()
            animated_msg("Wrong!",answer_space.x,answer_space.y,function(){})        
    }
    
}  

function add_coin(option_obj,call_fn){
    coin_bitmap=draw_bitmap(option_obj.x,option_obj.y,images.coin,max_height=30,max_width=30)
    stage.addChild(coin_bitmap)
    score_icon=get_child(stage,"score_icon")
    createjs.Tween.get(coin_bitmap, {loop: 0})
    .to({x: score_icon.x, y: score_icon.y}, 1000, createjs.Ease.bounceOut) 
    .call(function(){
        score_txt=get_child(stage,"score_txt")
        score_txt.text=""+user.score
        call_fn()

    })
    
}

function add_life(option_obj,call_fn){
    heart_bitmap=draw_bitmap(option_obj.x,option_obj.y,images.heart,max_height=30,max_width=30)
    stage.addChild(heart_bitmap)
    //life_icon=get_child(stage,"score_icon")
    lives_icon=get_child(stage,"lives_icon")
    createjs.Tween.get(heart_bitmap, {loop: 0})
    .to({x: lives_icon.x, y: lives_icon.y}, 1000, createjs.Ease.bounceOut) 
    .call(function(){
        lives_txt=get_child(stage,"lives_txt")
        lives_txt.text=""+user.lives
        call_fn()

    })
    
}

function check_answer_multi(evt){
    trg=evt.currentTarget
    selected_answer=trg.name
    if (question.answers==null) question.answers=[] 
    cur_i=question.answers.length //current position of the answer
    if (selected_answer==question.correct[cur_i]){
        //correct answer
        trg.children[0].graphics._fill.style="green"
        question.answers.push(trg.name)
        answer_x_offset=w/(question.correct.length+1) //information to help us animate
        answer_space=get_child(stage,"answer_space")
        if (quiz.rtl==true) answer_x=w-answer_x_offset*question.answers.length //if we are comining arabic letters >>rtl
        else answer_x=answer_x_offset*question.answers.length //if we are comning latin letters not rtl
        createjs.Tween.get(trg, {loop: 0})
        .to({x: answer_x, y: answer_space.y}, 1000, createjs.Ease.bounceOut)  
        .call(function(){
            if (question.answers.length==question.correct.length){
                quiz.i+=1
                animated_msg("Correct!",answer_space.x,answer_space.y+100,function(){
                    question.answers=[]
                    if (quiz.i>=quiz.n) alert("Level Complete!")
                    else deploy_q_multi()             
                })                  
            }
          
           //this.parent.removeChild(this) 
            //callback_fn()
            //gen_lesson_quiz()
        })  
        
        
    }
    else {
        //wrong answer 
        shake_horizontal(trg,100)
    }
    
    //question.correct=[1,2,3,4]  
}

function wrong_answer(){
    user.lives-=1
    if (user.lives==0) game_over()
    lives_txt=get_child(stage,"lives_txt")
          
    lives_bmp=get_child(stage,"lives_icon")
    lives_bmp.image=images.broken_heart
    createjs.Tween.get(lives_txt, {loop: 0})
    .to({scaleX:0.1,scaleY:0.1},500)
    //.wait(1000)
    .call(function(){
        lives_bmp.image=images.heart
        lives_txt.scaleX=1
        lives_txt.scaleY=1
        lives_txt.text=""+user.lives 
     
    })
    
}

function game_over(){
    check_high_score()
    user.score=0;
    user.lives=5 //should be dynamic
    
    animated_msg("Game Over!",w/2,h/2,function(){
        go2game()
    },5000)     
    
    //alert("Game Over!")

    
}

function check_high_score(){
    
}

function check_quiz_answer(obj){
    trg=obj.currentTarget
    //alert(trg.name)
    if (trg.name==question.correct) {
        quiz.i+=1
        trg.children[0].graphics._fill.style="green"
        animated_msg("Correct!",w/2,h/2,function(){
            if (quiz.i>=quiz.n) quiz_complete()
            else deploy_lesson_quiz()             
        })
    }
    else {
            trg.children[0].graphics._fill.style="red"
            animated_msg("Wrong!",w/2,h/2,function(){})        
    }
}   

function quiz_complete(){
    lvl_complete_text=draw_text(w/2,h/2,"Quiz Completed!",txt_style="bold 24px Comic",txt_color="#000")
    stage.addChild(lvl_complete_text)        
    createjs.Tween.get(lvl_complete_text, {loop: 0})
    .to({scaleX: 2, scaleY: 2}, 1000, createjs.Ease.bounceOut)  
    .call(function(){
       this.parent.removeChild(this) 
        //start_lvl1()
        start_level(level.main_id)
        
        //gen_lesson_quiz()
    })   
    
}



//The first three levels have a level map that is loaded when you start the level
//function start_lvl1(){
//    clean()
//    cur_level_container=draw_levels(game_data.alphabet_sublevels,start_alphabet_sublevel, 0,100,w,h-100,user.completed_level_ids, bubble_radius=50)
//    draw_header("Alphabet")
//    stage.addChild(cur_level_container)  
//}
//
//function start_lvl2(){
//    clean()
//    cur_level_container=draw_levels(game_data.diacritics_sublevels,start_diacritics_sublevel, 0,100,w,h-100,user.completed_level_ids, bubble_radius=50)   
//    draw_header("Diacritics")
//    stage.addChild(cur_level_container)      
//}
//
//function start_lvl3(){
//    clean()
//    cur_level_container=draw_levels(game_data.sounds_sublevels,start_sounds_sublevel, 0,100,w,h-100,user.completed_level_ids, bubble_radius=50)
//    draw_header("Sounds")
//    stage.addChild(cur_level_container)   
//}
//
//
////populate the level object with the current sublevel data, upon selecting a sublevel
//function set_level_data(sublevel_items,level_id,level_name){ 
//    level.sublevel_ids=Object.keys(sublevel_items)
//    level.items=sublevel_items[level_id]
//    level.item_ids=[]
//    for (it in level.items) level.item_ids.push(level.items[it].id)
//    level.n=level.items.length
//    level.i=0 //now updating the level object with the info of current sublevel
//    level.id=level_id; //main level ID
//    level.name=level_name  
//}
//
//function start_alphabet_sublevel(obj){
//    lvl_name=obj.currentTarget.name
//    lvl_id=obj.currentTarget.id    
//    sublevel_items=game_data.alphabet_lessons
//    set_level_data(sublevel_items,lvl_id,lvl_name)
//    
////    level.sublevel_ids=Object.keys(game_data.alphabet_lessons)
////    //level.sublevel_ids=game_data.alphabet_lessons.map(a => a.id) //add the ids of the sublevels to the level object
////    
////    
////    level.items=sublevel_items[lvl_id]
////    level.item_ids=[]
////    for (it in level.items) level.item_ids.push(level.items[it].id)
////    level.n=level.items.length
////    level.i=0 //now updating the level object with the info of current sublevel
////    level.id=lvl_id; //main level ID
////    
////    level.name=lvl_name
//
//    //alert(lvl_name+"+"+lvl_id)
//    //alert(JSON.stringify())
//    deploy_lesson(lvl_id)
//}
//
//
//
//function start_diacritics_sublevel(obj){
//    lvl_name=obj.currentTarget.name
//    lvl_id=obj.currentTarget.id    
//    sublevel_items=game_data.diacritics_lessons
//    set_level_data(sublevel_items,lvl_id,lvl_name)
////    
////    level.sublevel_ids=Object.keys(game_data.diacritics_lessons)
////    level.items=sublevel_items[lvl_id]
////    level.item_ids=[]
////    for (it in level.items) level.item_ids.push(level.items[it].id)
////    level.n=level.items.length
////    level.i=0 //now updating the level object with the info of current sublevel
////    level.id=lvl_id; //main level ID
////    level.name=lvl_name
//    
//    deploy_lesson(lvl_id)
//}
//
//
//function start_sounds_sublevel(obj){
//    lvl_name=obj.currentTarget.name
//    lvl_id=obj.currentTarget.id    
//    sublevel_items=game_data.sound_lessons
//    set_level_data(sublevel_items,lvl_id,lvl_name)
//    
////    level.sublevel_ids=Object.keys(game_data.diacritics_lessons)
////    level.items=sublevel_items[lvl_id]
////    level.item_ids=[]
////    for (it in level.items) level.item_ids.push(level.items[it].id)
////    level.n=level.items.length
////    level.i=0 //now updating the level object with the info of current sublevel
////    level.id=lvl_id; //main level ID    
////    level.name=lvl_name
//    
//    deploy_lesson(lvl_id)
//}
//
//
//function deploy_lesson_OLD(main_level_id){
//    clean()
//    draw_header("Alphabet")
//    cur_sublevel_item=level.items[level.i]
//    console.log(cur_sublevel_item)
//    letter_txt_str1=cur_sublevel_item.arabic_script 
//    //letter_txt1=draw_text(w/2,100,letter_txt_str1,txt_style="bold 48px Comic",txt_color="red")
//    //draw_bubble(w/2,100,letter_txt_str1,txt_style="bold 48px Comic",txt_color="#000")
//    if (letter_txt_str1!=""){
//        letter_txt1=draw_bubble(w/2,100,text=letter_txt_str1,img_obj=null,color="red",radius=25,style="bold 36px Arial",img_scale=0.75)
//        stage.addChild(letter_txt1)
//        
//    }
//    
//    
//    letter_txt_str2=cur_sublevel_item.letter_name  //QINFO
//    letter_txt2=draw_text(w/2,150,letter_txt_str2,txt_style="bold 24px Comic",txt_color="#000")  
//    shapes_str=""
//    if (cur_sublevel_item.letter_shapes!="") shapes_str="Letter shapes:\n"+cur_sublevel_item.letter_shapes
//    letter_shapes_txt=draw_text(w/2,200,shapes_str ,txt_style="bold 24px Comic",txt_color="#000")  
//
//    examples_str=""
//    if (cur_sublevel_item.examples!="") shapes_str="Examples:\n"+cur_sublevel_item.examples
//    examples_txt=draw_text(w/2,250,shapes_str ,txt_style="bold 24px Comic",txt_color="#000")  
//    examples_split=split(cur_sublevel_item.examples)
//    x_offset=w/(examples_split.length+1)
//    x0_=x_offset
//    for (ex in examples_split){
//        ex_str=examples_split[ex]
//        ex_color=getRandomColor()
//        ex_btn=draw_button(x0_,280,ex_str,"",ex_color,60,50,5)
//        ex_btn.name=ex_str
//        ex_btn.on("click",function(evt){
//            name=evt.currentTarget.name
//            alert(name.split("").join(" "))
//        })
//        stage.addChild(ex_btn)
//        x0_+=x_offset
//    }
//    
//    desc_multiline=multiline(cur_sublevel_item.description,25)
//
//    desc_txt=draw_text(w/2,0.7*h,desc_multiline,txt_style="bold 24px Comic",txt_color="#000")
//    next_btn=draw_button(w/2,0.9*h,"Next","","purple",100,60,5)
//    next_btn.on("click",next_lesson)
//    
//    stage.addChild(letter_txt2,letter_shapes_txt,desc_txt,next_btn)
//    
//    //Get the list of shapes - we can do this from the pandas export
//    cur_sublevel_item.shapes_list=[]
//    tmp_shape_split=$.trim(cur_sublevel_item.letter_shapes).split(" ")
//    for (ts in tmp_shape_split) cur_sublevel_item.shapes_list.push($.trim(tmp_shape_split[ts])) //to avoid spaces
//    
//    cur_sublevel_item["main_level"]=level.main_id
//    
//    //add to what the user has learned
//    if (letter_txt_str1=="") return
//    if (user.completed_items_ids==null || user.completed_items_ids==undefined) user.completed_items_ids=[]
//    if (user.completed_items==null || user.completed_items==undefined) user.completed_items={}
//    
//    cur_id=cur_sublevel_item.id
//    if (user.completed_items_ids.indexOf(cur_id)==-1){
//        user.completed_items_ids.push(cur_id)
//        user.completed_items[cur_id]=cur_sublevel_item
//    }
//    
////    tmp_item={} //to keep the main info of the sublevel to be used in quizzes
////    tmp_item
////    user.completed_levels.push(cur_sublevel_item)
////    //alert(JSON.stringify(cur_sublevel_item))
//    
//    
//}
//
//function next_lesson_OLD(){
//    level.i+=1
//    if (level.i>=level.n) lesson_complete()
//    else deploy_lesson()
//}
//
//function lesson_complete_OLD(){
//    clean()
////    console.log(user.completed_items_ids)
////    console.log(user.completed_items)
////    if (user.completed_level_ids==null || user.completed_level_ids==undefined) user.completed_level_ids=[]
////    if (user.completed_level_ids.indexOf(level.id)==-1) user.completed_level_ids.push(level.id)
//    
//    user.completed_level_ids=push(user.completed_level_ids,level.id)
//    level_is_complete=true
//    for (it in level.sublevel_ids){
//        cur_sublevels_id=level.sublevel_ids[it]
//        if (user.completed_level_ids.indexOf(cur_sublevels_id)==-1) level_is_complete=false
//    }
//    if (level_is_complete) user.completed_level_ids=push(user.completed_level_ids,level.main_id)
//    //user.completed_level_ids=push(user.completed_level_ids,level.main_id)
//    //user.completed_level_ids=push(user.completed_level_ids,level_id)
//    
//    lvl_complete_text=draw_text(w/2,h/2,"Lessons Completed!",txt_style="bold 24px Comic",txt_color="#000")
//    stage.addChild(lvl_complete_text)        
//    createjs.Tween.get(lvl_complete_text, {loop: 0})
//    .to({scaleX: 2, scaleY: 2}, 1000, createjs.Ease.bounceOut)  
//    .call(function(){
//       this.parent.removeChild(this) 
//        //deploy_sublevels1()
//        gen_lesson_quiz()
//    })    
//}

function gen_lesson_quiz(){
    cur_items=level.items
    cur_ids=level.item_ids
    all_completed_ids=user.completed_items_ids
    console.log(all_completed_ids)
    cur_level_copmpleted_items=filter_list(user.completed_items,"main_level",level.main_id)
    cur_level_completed_ids=cur_level_copmpleted_items.map(a => a.id)
    
    console.log(cur_level_completed_ids)
    
    quiz_pre_n=5 //number of questions from previous sublevels
    quiz.questions=[]
    quiz.i=0
    for (id0 in cur_ids){
        item_id=cur_ids[id0]
        item_obj=user.completed_items[item_id]
        if (item_obj==null || item_obj==undefined) continue
        //cur_options=gen_options(item_id,all_completed_ids,n_options=4)
        cur_options=gen_options(item_id,cur_level_completed_ids,n_options=4)
        cur_shape=shuffle(item_obj.shapes_list)[0]
        cur_name=item_obj.letter_name
        q_type=shuffle(["name2shape","shape2name"])[0] //randomize question types
            
        //q_types=["name2shape","shape2name"] //different question types
        //shuffle(q_types) 
        
        quiz_q={}
        
        if (true){
            quiz_q.prompt="which is this?"
            quiz_q.item=cur_name
            quiz_q.correct_answer=cur_shape
            quiz_q.options=[cur_shape]
            for (op in cur_options){
                op_id=cur_options[op]
                if (op_id==item_id) continue
                op_obj=user.completed_items[op_id]
//                cur_op_shapes_tmp=op_obj.shapes_list
//                shuffle(cur_op_shapes_tmp)
//                cur_op_shape=cur_op_shapes_tmp[0]
                cur_op_shape=shuffle(op_obj.shapes_list)[0]
                quiz_q.options.push(cur_op_shape)
            }
        } //randomize question type
//        if (q_types[0]=="name2shape")
        quiz.questions.push(quiz_q)
        //console.log(quiz_q)
        //console.log(item_obj,cur_options)
        
    }
    quiz.n=quiz.questions.length
    deploy_lesson_quiz()
}

function deploy_lesson_quiz(){
    clean()
    draw_header("Quiz")
    cur_question=quiz.questions[quiz.i]
    question.correct=cur_question.correct_answer
    
    mcq_container=deploy_mcq(cur_question.prompt,cur_question.item,cur_question.options,check_quiz_answer,layout=0)
    stage.addChild(mcq_container)
 
}


//Keyboard levels
//var kb_txt;
//function start_lvl4(){
//    show_screen("main_canvas")
//    draw_header("Level 4")
//    //kb_txt=draw_text(w/2,h/3,"",txt_style="bold 24px Comic",txt_color="#000")
//    kb=draw_keyboard(game_data.keyboard_dict, 0,h/2,w,h/4,test_kb,25)
//    stage.addChild(kb,kb_txt)    
//    
//    //stage.addChild(text1)
//    stage.update() 
//    
//}

//function test_kb(obj){
//    text=kb_txt.text
//    if (obj.currentTarget.name=="back") text = text.substring(0, text.length - 1);
//    else text+=obj.currentTarget.name
//    kb_txt.text=text
//    
//    //alert(obj.currentTarget.name)
//    stage.update()
//}

//
//
//function start_lvl5(){
//    
//}
//
//function start_lvl6(){
//    
//}
//
//function start_lvl7(){
//    
//}
//
//function start_lvl8(){
//    
//}
//
//function start_lvl9(){
//    
//}