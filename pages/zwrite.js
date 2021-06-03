var auto_draw=false;
var label, shape, oldX, oldY, size, color;
var writing_list=[]

function makeWriting(stage) {
    var stageW = stage.width;
    var stageH = stage.height;
    var page = new Page(stageW, stageH, blue,green);
    page.i=0;
    STYLE = {font:"reuben", size:50};
    
    
    
    
    page.timer=new Label({color:purple, text:"Writing", size:48,variant:true}).pos(0,30,CENTER,TOP,page);
    //page.accuracy=new Label({color:purple, text:"100%", size:48,variant:true, align:RIGHT}).pos(30,30,RIGHT,TOP,page);
    
    menu_label=new Label({color:yellow, text:"Menu", size:25, align:CENTER})
    page.go2menu = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:menu_label,corner:20})
    .pos(30,30,LEFT,TOP,page)  

//    next_label=new Label({color:yellow, text:"Next", size:25, align:CENTER})
//    page.next = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:next_label,corner:20})
//    .pos(0,30,CENTER,BOTTOM,page)
     
//    writing_letters_label=new Label({color:yellow, text:"Letters", size:60, align:CENTER})
//    page.start_writing = new Button({width:350,height:100,backgroundColor:purple,rollBackgroundColor:orange,label:writing_letters_label,corner:20})
//    .pos(0,-200,CENTER,CENTER,page)
//
//    writing_words_label=new Label({color:yellow, text:"Words", size:60, align:CENTER})
//    page.start_writing = new Button({width:350,height:100,backgroundColor:purple,rollBackgroundColor:orange,label:writing_words_label,corner:20})
//    .pos(0,200,CENTER,CENTER,page)
//    
//    start_writing_label=new Label({color:yellow, text:"Letter Shapes", size:60, align:CENTER})
//    page.start_writing = new Button({width:350,height:100,backgroundColor:purple,rollBackgroundColor:orange,label:start_writing_label,corner:20})
//    .center(page)
//    .tap(function(evt){
//        trg=evt.currentTarget
//        remove_el(trg)
//        page.prepare()
//        page.deploy()
//    })
//    page.prepare=function(){
//        //remove_el(page.start_writing)
//        for (const let_id of game_data.all_ids){
//            cur_name=game_data.name_dict[let_id]
//            if (cur_name==null || cur_name=="") continue
//            letter_ar_script=game_data.letter_dict[let_id].arabic_script
////            cur_let_shapes=game_data.shape_dict[let_id].slice(0,4)
////            cur_let_shapes.reverse()
////            cur_shape=cur_let_shapes.join(" ") //we should expand to all the shapes
//            
//            writing_list.push({id:let_id,shape:letter_ar_script,name:cur_name})
//        }
//        zog(writing_list)
//    }
    
    
    page.deploy=function(){
        remove_el(page.main_cont)
        stage.removeAllEventListeners()
        
        stage.autoClear = true;
        createjs.Touch.enable(stage);
        shape = new createjs.Shape();
        cur_writing_item=quiz.writing_list[page.i]

        page.main_cont = new Container(stageW, stageH).addTo(page);

        prompt_text="Write"
        
        
        page.prompt=new Label({color:red, text:cur_writing_item.name, size:48,variant:true}).pos(0,100,CENTER,TOP,page.main_cont);
        page.example=new Label({color:purple, text:cur_writing_item.shape, size:72,variant:true}).pos(0,150,CENTER,TOP,page.main_cont);
        page.instructions=new Label({color:purple, text:"Swipe on the screen\nto draw in the box below", size:25,variant:true, align:CENTER}).pos(0,225,CENTER,TOP,page.main_cont);  
        
        let rect0 = new Rectangle(stageW*0.8,stageH*0.5,orange).pos(0,100,CENTER,BOTTOM,page.main_cont);
        
        page.main_cont.addChild(shape);    
        console.log(shape)

        color = "#000";
        stroke = 5;

        //stage.on("stagemousemove",function(evt) {
        stage.on("pressmove",function(evt) {
            if (oldX) {
                shape.graphics.beginStroke(color)
                              .setStrokeStyle(stroke, "round")
                              .moveTo(oldX, oldY)
                              .lineTo(evt.stageX, evt.stageY);
                stage.update();
            }
            oldX = evt.stageX;
            oldY = evt.stageY;
        })
        stage.addEventListener("stagemouseup", function(){
            oldX = null;
            oldY = null;

        });    
        next_label=new Label({color:yellow, text:"Next", size:25, align:CENTER})
        page.next = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:next_label,corner:20})
        .pos(0,30,CENTER,BOTTOM,page.main_cont)
        .tap(function(){
            page.i+=1
            if (page.i>=quiz.writing_list.length) return
            page.deploy()
        })
        //remove_el(page.main_cont)        
    }
    

    stage.update(); // this is needed to show any changes
    
//    next_label=new Label({color:yellow, text:"Next", size:25, align:CENTER})
//    page.next = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:next_label,corner:20})
//    .pos(0,30,CENTER,BOTTOM,page)
    
    return page;
    
    ///////
    
    game_ended_label=new Label({color:yellow, text:"After Game", size:25, align:CENTER})
    page.go2after_game = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:game_ended_label,corner:20})
    .pos(0,30,CENTER,BOTTOM,page).alp(0)
    
    var emitter = new Emitter({
        obj:new Poly([10,20,30], 5, .6, [pink, purple, dark, purple]),
        num:5,
        gravity:0,
        force:{min:3, max:5},
        startPaused:true
    }).addTo(page).bot().ord(1); // put under the animals but above the page backing
    

    
    q_obj1={}
    q_obj1.deploy_fn=page.deploy_q
    q_obj1.prompt="What is the name of this letter?"
    q_obj1.item={label:"أ",id:"alif"}
    q_obj1.correct=["alif"]
    q_obj1.options=[{label:"alif",id:"alif"},
                   {label:"hamzah 3ala nabrah",id:"hamzah_3ala_nabrah"},
                   {label:"seen",id:"seen"},
                   {label:"kaaf",id:"kaaf"}
                  ]
    q_obj2={}
    q_obj2.deploy_fn=page.deploy_q
    q_obj2.prompt="Which letter os this?"
    q_obj2.item={label:"kaaf",id:"kaaf"}
    q_obj2.correct=["kaaf"]
    q_obj2.options=[{label:"أ",id:"alif"},
                   {label:"ع",id:"3ayn"},
                   {label:"س",id:"seen"},
                   {label:"ك",id:"kaaf"}
                  ]
    quiz.questions=[q_obj1,q_obj2]
    quiz.i=0;
    //function deploy_q(q_obj)
    page.deploy_q=function(q_obj){
        remove_el(page.main_cont)
        page.main_cont = new Container(stageW, stageH).addTo(page);
        q_n=quiz.i+1
        tmp_prompt=""+q_n+"- "+ q_obj.prompt
        prompt_txt=multiline(tmp_prompt,20)
        page.prompt=new Label({color:purple, text:prompt_txt, size:36,variant:true, align:CENTER}).pos(0,100,CENTER,TOP,page.main_cont);
        
        item_text=multiline(q_obj.item.label,5)
        if (item_text.length>3) item_font_size=60
        else item_font_size=120
        page.item=new Label({color:purple, text:item_text, size:item_font_size, align:CENTER}).center(page.main_cont);
        page.item.id=q_obj.item.id
//        page.item.tap(function(evt){
//            trg=evt.currentTarget;
//            console.log(trg.id)
//            //main_cont.parent.removeChild(main_cont)
//        })

        var options_tile = page.options_tile = new Tile({
            obj:new Container(200,200).centerReg({add:false}),
            cols:2,
            rows:2,
            spacingH:200,
            spacingV:150,
            valign:CENTER
        })
            .sca(1)
            //.ble("multiply")
            .center(page.main_cont)
            .mov(0,50);
        shuffle(q_obj.options)
        options_tile.loop(function (op, i){
            //console.log(op)
            cur_option_obj=q_obj.options[i]
            //console.log(cur_option_obj)
            option_txt=cur_option_obj.label
            option_txt_ml=multiline(option_txt,7)
            if (option_txt.length>10) font_size=25
            else font_size=40
            op_btn_label=new Label({color:white, text:option_txt_ml, size:font_size, align:CENTER})//.pos(0,-100,CENTER,CENTER,page1);
            var cur_op_btn = new Button({width:150,height:140,backgroundColor:blue,rollBackgroundColor:orange,label:op_btn_label,corner:10})
            .center(op);
            cur_op_btn.id=cur_option_obj.id
            cur_op_btn.on("mousedown",check_answer)
        })        
    }
    cur_q_obj=quiz.questions[quiz.i]
    page.deploy_q(cur_q_obj)

//        quiz.accuracy=0
//        quiz.n_attempts=0
//        quiz.n_correct=0
//        game.accuracy.text=""+quiz.accuracy+"%"
    
    function check_answer(evt){
        
        trg=evt.currentTarget
        console.log(trg.id)
        //console.log(frame.asset(trg.id))
        frame.asset(trg.id).play()
        quiz.n_attempts+=1
        if (trg.id==page.item.id){
            console.log("correct!")
            quiz.n_correct+=1
            trg.backgroundColor=green
            emitter.loc(trg, null, page).spurt(100);
            trg.animate({
                wait:0.2, // wait one second before starting
                props:{scale:1.5},
                time:.5,
                rewind:true,
                loop:false,
                loopCall:()=>{next_q()} // also call, rewindCall, and more
            });

            
        }
        else {
            
            trg.removeAllEventListeners()
            console.log("wrong!")
            trg.backgroundColor=red
            
        }
        quiz.accuracy=quiz.n_correct/quiz.n_attempts
        accuracy_100=Math.round(100*quiz.accuracy) 
        page.accuracy.text=""+accuracy_100+"%"
        
        if (quiz.accuracy>0.75) page.accuracy.color="green"
        else if (quiz.accuracy>0.5) page.accuracy.color=orange.darken(0.5)
        else page.accuracy.color="red"
    }    
    
    function next_q(){
        //remove_el(page.main_cont)
        quiz.i+=1;
        if (quiz.i>=quiz.questions.length){
            pages.go(after_game, "down");
            game_ended()
            return
        }
        cur_q_obj=quiz.questions[quiz.i]
        page.deploy_q(cur_q_obj)        
        zog("deploy next Q")
        
    }    

    
    return page;

}


function game_ended(){
    after_game.completion_label.text="Completed: "+quiz.n_correct+" questions"   
    accuracy_100=Math.round(100*quiz.accuracy)
    after_game.accuracy_label.text="Accuracy: "+accuracy_100+"%"   
    score=Math.round(10*quiz.n_correct*quiz.accuracy) 
    after_game.score_label.text="Score: "+score 
    
    
}


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
//        tmp_q_obj.deploy_fn=deploy_q
//        tmp_q_obj.check_fn=check_answer
        q_types=["name2shape","shape2name"]
        cur_q_type=shuffle(q_types)[0]
        tmp_q_obj.type=cur_q_type
        if (cur_q_type=="name2shape"){
            tmp_q_obj.prompt="Which letter is this?"
            tmp_q_obj.item={label:name_dict[cur_id], id:cur_id}  
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
            cur_item_label=shuffle(shape_dict[cur_id])[0]
            tmp_q_obj.item={label:cur_item_label,id:cur_id} //name_dict[cur_id]  
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
        //console.log(tmp_q_obj)
    }
    quiz.n=quiz.questions.length;
}



function gen_sound_questions(){
    quiz.questions=[]
    quiz.i=0;
    sound_ids=game_data.sound_ids
    sound_dict=game_data.sound_dict
    sound_ids_copy=shuffle(copy(sound_ids))
    //console.log(sound_ids_copy)
    for (const sid of sound_ids_copy){
        cur_obj=sound_dict[sid]
        //console.log(sid,cur_obj)
        options=gen_options(sid,sound_ids,n_options=4)
        tmp_q_obj={}
        tmp_q_obj.prompt="What sound does this letter make?"
        tmp_q_obj.item={label:cur_obj.arabic, id:sid}  
        tmp_q_obj.options=[]
        tmp_q_obj.correct=options[0]
        for (op in options){
            op_id=options[op]
            op_tmp_obj=sound_dict[op_id]
            op_obj={}
            
            //op_shape=shuffle(shape_dict[op_id])[0] 
            op_obj.id=op_id
            op_obj.label=op_tmp_obj.sound
            op_obj.name=op_tmp_obj.sound
            tmp_q_obj.options.push(op_obj)
        }   
        //zog(tmp_q_obj)
        quiz.questions.push(tmp_q_obj)
    }
    return 
    
    //test=game_data.alphabet_lessons.map(a => a.id)
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
//        tmp_q_obj.deploy_fn=deploy_q
//        tmp_q_obj.check_fn=check_answer
        q_types=["name2shape","shape2name"]
        cur_q_type=shuffle(q_types)[0]
        tmp_q_obj.type=cur_q_type
        if (cur_q_type=="name2shape"){
            tmp_q_obj.prompt="Which letter is this?"
            tmp_q_obj.item={label:name_dict[cur_id], id:cur_id}  
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
            cur_item_label=shuffle(shape_dict[cur_id])[0]
            tmp_q_obj.item={label:cur_item_label,id:cur_id} //name_dict[cur_id]  
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
