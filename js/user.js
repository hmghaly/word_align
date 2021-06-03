//Functions related to collecting and updating user info

function deploy_profile(){
    profile_div=$$("profile_div")
    profile_div.innerHTML=""
    profile_header=create_el("h2",profile_div,"profile_header","profile_header","Your Profile")
    enter_email_p=create_el("p",profile_div,"enter_email_p","enter_email_p","Enter your email below to receive updates and notifications:")
    user_email_input=create_el("input",profile_div,"email","email","")
    user_email_input.placeholder="Your Email Address"
    user_email_input.className="form-control-inline"
    console.log(user)
    //user.email="aa@bb.cc"
    email_button_txt="Submit Email"
    if (user.email!=null && user.email!="") {
        user_email_input.value=user.email
        email_button_txt="Update Email"
    } 
    submit_email_button=create_el("button",profile_div,"submit_email","submit_email",email_button_txt)
    submit_email_button.onclick=submit_email
    submit_email_button.style.width="150px"
    hr1=create_el("hr",profile_div,"","","")
    
    enter_username_p=create_el("p",profile_div,"enter_username_p","enter_username_p","Choose a username: ")
    username_status_span=create_el("span",enter_username_p,"username_status_span","username_status_span","")
    user_username_input=create_el("input",profile_div,"username","username","")
    user_username_input.placeholder="Choose a username"
    user_username_input.className="form-control-inline"
    user_username_input.addEventListener('change',function(){
        username_status_span=$$("username_status_span")
         username_status_span.innerHTML=""
        username=$$("username").value
        user.username=username
        console.log(username)
        set_local_strorage(storage_name,"user",user)
        $(".username").html(username)
        username_status_span.style.color="green"
        username_status_span.innerHTML="updated successfully!"
        //$$("enter_username_p").innerHTML+='<span style="color:Green;"> updated successfully!</span>'
    })
    //user_username_input.setAttribute("max_length", 10)
    //user.username="user1"
    //username_button_txt="Submit Username"
    if (user.username!=null && user.username!="") {
        user_username_input.value=user.username
        //username_button_txt="Update Username"
    } 
//    submit_username_button=create_el("button",profile_div,"submit_username","submit_username",username_button_txt)
//    submit_username_button.onclick=update_username
//    submit_username_button.style.width="150px"
    
    //Now for chooseing the avatar
    //user.avatar_src="../img/avatars/001-girl-10.png"
    choose_avatar_p=create_el("p",profile_div,"choose_avatar_p","choose_avatar_p","Choose an avatar:<br>")
    current_avatar_img=new Image()
    current_avatar_img.src="../img/user.png"
    if (user.avatar_src!=null && user.avatar_src!="") current_avatar_img.src=user.avatar_src
    current_avatar_img.width=100 
    current_avatar_img.className="avatar user_avatar"
    choose_avatar_p.appendChild(current_avatar_img)
    avatar_gallery_p=create_el("p",profile_div,"avatar_gallery_p","avatar_gallery_p","")

    avatar_src_list=["../img/user.png","../img/avatars/001-girl-10.png","../img/avatars/002-girl-9.png","../img/avatars/003-boy-20.png","../img/avatars/018-boy-13.png","../img/avatars/037-girl-1.png","../img/avatars/005-girl-7.png","../img/avatars/010-boy-19.png", "../img/avatars/035-boy-6.png",  "../img/avatars/005-prince.png","../img/avatars/009-ninja.png","../img/avatars/011-joker.png"]
    for (const tmp_avatar_src of avatar_src_list){
        current_avatar_img=new Image()
        current_avatar_img.src=tmp_avatar_src
        current_avatar_img.name=tmp_avatar_src
        current_avatar_img.className="avatar"
        if (user.avatar_src==tmp_avatar_src) current_avatar_img.className="avatar selected_avatar"
        current_avatar_img.width=50 
        current_avatar_img.onclick=function(){
            input_class_name="selected_avatar"
            $(".selected_avatar").removeClass("selected_avatar");
            this.classList.add(input_class_name)
            user.avatar_src=this.name
            set_local_strorage(storage_name,"user",user)
            $(".user_avatar").attr("src",user.avatar_src)
            
        }
        avatar_gallery_p.appendChild(current_avatar_img)        
    }
    continue_button=create_el("button",profile_div,"continue_button","continue_button","Continue")
    continue_button.className="btn btn-primary btn-block"
    continue_button.onclick=function(){
        username=$$("username").value
        if (username=="") {
            alert("Please choose a username")
            return
        }
        go2menu()
    }

}    




//function select_avatar(obj){ //apply class "selected_avatar" to the clicked avatar picture and remove it from any previously selected one
//    input_class_name="selected_avatar"
//    $(".selected_avatar").removeClass("selected_avatar");
//    obj.classList.add(input_class_name)
//    avatar_src=obj.src
//    console.log(avatar_src)
//    set_local_strorage(storage_name,"avatar_src",avatar_src)
//    $(".user_avatar").attr("src",avatar_src)
//}

function update_username(){ //update username 
    username=$$("username").value
    user.username=username
    console.log(username)
    set_local_strorage(storage_name,"user",user)
    $(".username").html(username)
    $$("enter_username_p").innerHTML+='<span style="color:Green;"> updated successfully!</span>'
    
}

function submit_email(){
    email_str=$.trim($$("email").value)
    is_email=check_email_str(email_str)
    if (!is_email) alert("invalid email address: "+ email_str)
    else {
        $$("enter_email_p").innerHTML+='<span style="color:Green;"> updated successfully!</span>'
        user.email=email_str
        set_local_strorage(storage_name,"user",user)
        email_obj={}
        email_obj["email"]=email_str
        email_obj["assigned_user_key"]=assigned_user_key
//        var time_date = new Date();
//        email_obj["time"]=time_date
        email_obj["time"]=Date.now()
        email_obj["app"]=game_name //need to be set
        email_obj["action"]="submit_email"
        
        console.log(email_obj) //"../login_signup.py"
        //callback_fn()
        link="../../get_email.py"
        post_data(link,email_obj,function(obj1){
            console.log(obj1)
        })                
        
    }
    
}



//function submit_email2(link,callback_fn){
//    email_str=$.trim($$("email").value)
//    is_email=check_email_str(email_str)
//    if (!is_email) alert("invalid email address: "+ email_str)
//    else {
//        user.email=email_str
//        set_local_strorage(storage_name,"user",user)
//        email_obj={}
//        email_obj["email"]=email_str
//        var time_date = new Date();
//        email_obj["time"]=time_date
//        email_obj["game_name"]=game_name //need to be set
//        email_obj["action"]="submit_email"
//        
//        console.log(email_obj) //"../login_signup.py"
//        callback_fn()
//        post_data(link,email_obj,callback_fn)                
//        
//    }
//    
//}


function load_user_info(){
    //from local storage
    user=get_local_strorage(storage_name,"username")
//    found_username=get_local_strorage(storage_name,"username")
//    if (found_username!="null"){
//        username=found_username
//        $(".username").html(username)
//        $$("username_input").value=username        
//    }
//
//    found_avatar_src=get_local_strorage(storage_name,"avatar_src")
//    if (found_avatar_src!="null"){
//        avatar_src=found_avatar_src
//        $(".user_avatar").attr("src",avatar_src)
//    }
}