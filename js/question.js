function gen_shape_questions(){
    quiz.questions=[]
    quiz.i=0;
    all_ids=game_data.letter_ids
    shape_dict=game_data.shape_dict
    name_dict=game_data.name_dict
    
    new_all_ids=all_ids.concat(all_ids);
    new_all_ids=new_all_ids.concat(all_ids);
    new_all_ids=shuffle(new_all_ids)
    
    all_q_options=[]
    for (lt in new_all_ids){
        cur_id=new_all_ids[lt]
        cur_shape=shape_dict[cur_id]
        options=gen_options(cur_id,all_ids,n_options=4)
        all_q_options.push(options)  
        tmp_q_obj={}
        tmp_q_obj.deploy_fn=deploy_mcq
        tmp_q_obj.check_fn=check_mcq
        q_types=["name2shape","shape2name"]
        cur_q_type=shuffle(q_types)[0]
        if (cur_q_type=="name2shape"){
            tmp_q_obj.prompt="Which letter is this?"
            tmp_q_obj.item=name_dict[cur_id]  
            tmp_q_obj.options=[]
            tmp_q_obj.correct=options[0]
            for (op in options){
                op_obj={}
                op_id=options[op]
                op_shape=shuffle(shape_dict[op_id])[0] 
                op_obj.id=op_id
                op_obj.label=op_shape
                op_obj.name=op_shape
                tmp_q_obj.options.push(op_obj)
            }
                        
        }
        else if (cur_q_type=="shape2name"){
            tmp_q_obj.prompt="What is the name of this letter?"
            tmp_q_obj.item=shuffle(shape_dict[cur_id])[0] //name_dict[cur_id]  
            tmp_q_obj.options=[]
            tmp_q_obj.correct=options[0]
            for (op in options){
                op_obj={}
                op_id=options[op]
                op_name=name_dict[op_id] //shuffle(shape_dict[op_id])[0] 
                op_obj.id=op_id
                op_obj.label=op_name
                op_obj.name=op_name
                
                tmp_q_obj.options.push(op_obj)
            }            
            
        }
        
        quiz.questions.push(tmp_q_obj)        
        console.log(tmp_q_obj)
    }
    quiz.n=quiz.questions.length;
}

//MCQ type question flow: deploy >> check (correct/wrong)
function deploy_mcq(q_obj){
    if (quiz.finished) return
    //clean()
    //draw navigation header
    //draw game header
    //draw question layout
    //draw options >> with the check function at each option
    cur_q_container=get_child(stage,"q_container")
    if (cur_q_container!=null && cur_q_container!=undefined) cur_q_container.parent.removeChild(cur_q_container)
    
    
    q_x0=0
    q_y0=h/5
    q_w0=w
    q_h0=4*h/5
    check_fn=q_obj.check_fn
    console.log("loaded mcq")
    //cur_q_obj={prompt:"Hello",item:"item",options:["1","2","3","4"]}
    
    mcq_container=deploy_q_space_single(q_obj,q_x0,q_y0,q_w0,q_h0,check_fn) //from game.js
    mcq_container.name="q_container"
    stage.addChild(mcq_container)
    return mcq_container
} 

function check_mcq(evt){
    trg=evt.currentTarget
    trg.removeAllEventListeners()
    trg_id=trg.id
    aud_element_id="audio_"+trg_id
    $$(aud_element_id).play()
    
    trg.name=trg.name
    correct_answer=quiz.questions[quiz.i].correct
    answer_space=get_child(stage,"answer_space")
    if (quiz.n_attempts==null) quiz.n_attempts=0
    if (quiz.n_correct==null) quiz.n_correct=0
    quiz.n_attempts+=1
    
    
    if (correct_answer==trg_id) {
        
        quiz.n_correct+=1        
        if (user.score==null) user.score=0 //updating score
        user.score+=1          
        trg.children[0].graphics._fill.style="green"
        add_coin(trg,function(){})
        msg_txt="Correct!"
        mcq_correct(trg)
        animated_msg(msg_txt,answer_space.x,answer_space.y,next_q) 
    }
    else {
        if (quiz.mistakes==null) quiz.mistakes=[] //updating score
        cur_q_item=quiz.questions[quiz.i].item
        cur_mistake=[quiz.i,cur_q_item,trg.name]
        quiz.mistakes.push(cur_mistake)
        
        msg_txt="Wrong!"
        trg.children[0].graphics._fill.style="red"
        shake_horizontal(trg,100)
        mcq_wrong(trg)   
        animated_msg(msg_txt,answer_space.x,answer_space.y,function(){}) 
    }
     
    console.log(trg_id,correct_answer)
    update_accuracy()
    //next_q()
    
}

function update_accuracy(){
    console.log(quiz.n_correct,quiz.n_attempts)
    quiz.accuracy=Math.round(100*quiz.n_correct/quiz.n_attempts)
    accuracy_str=""+quiz.accuracy+"%"
    accuracy_txt_obj=get_child(stage,"accuracy_txt")
    accuracy_txt_obj.text=accuracy_str
}

function mcq_correct(selected_obj){
    
    
}

function mcq_wrong(selected_obj){
    
}

//Sequence type question flow: deploy >> check (correct/wrong)
function deploy_seq(q_obj){
    
}

function check_seq(selected_obj){
    
}

function seq_correct(selected_obj){
    
}

function seq_wrong(selected_obj){
    
}

//question and level progression
function next_q(){
    quiz.i+=1;
    if (quiz.i==quiz.n){
        alert("congratulations, you completed all the questions!")
        return
    }
    cur_q_obj=quiz.questions[quiz.i]
    cur_q_obj.deploy_fn(cur_q_obj)
}

function level_completed(){
    
}

function game_completed(){
    
}
function game_over(){
    
}

function submit_highscore(){
    
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
