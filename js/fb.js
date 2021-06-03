var facebook_info={}

  function statusChangeCallback(response) {  // Called with the results from FB.getLoginStatus().
    console.log('statusChangeCallback');
    console.log(response);                   // The current login status of the person.
    if (response.status === 'connected') {   // Logged into your webpage and Facebook.
      testAPI();  
    } else {                                 // Not logged into your webpage or we are unable to tell.
        console.log("unable to login to Facebook")
//      document.getElementById('status').innerHTML = 'Please log ' +
//        'into this webpage.';
    }
  }


  function checkLoginState() {               // Called when a person is finished with the Login Button.
    FB.getLoginStatus(function(response) {   // See the onlogin handler
      statusChangeCallback(response);
      console.log(response)
      //alert("Hello")
    });
  }


  window.fbAsyncInit = function() {
    FB.init({
      appId      : '543565049149582',
      cookie     : true,                     // Enable cookies to allow the server to access the session.
      xfbml      : true,                     // Parse social plugins on this webpage.
      version    : 'v8.0'           // Use this Graph API version for this call.
    });


    FB.getLoginStatus(function(response) {   // Called after the JS SDK has been initialized.
      statusChangeCallback(response);        // Returns the login status.
    });
  };
 
  function testAPI() {                      // Testing Graph API after login.  See statusChangeCallback() for when this call is made.
    console.log('Welcome!  Fetching your information.... ');
    FB.api('/me', { locale: 'en_US', fields: 'name, email,birthday, hometown,education,gender,website,work' }, function(response) {
    	console.log(response)
      console.log('Successful login for: ' + response.name);
      // document.getElementById('status').innerHTML =
      //   'Thanks for logging in, ' + response.name + '!';
      document.getElementById("fb_login_btn").innerHTML="Login with Facebook as "+response.name
      facebook_info=response
    });
  }

function fb_login(){
	// checkLoginState()
	console.log(facebook_info)
}
