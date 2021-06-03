client_id='ASancjQ-2tyudQRbadiBiox1Ul8LmZr0nXQwCCDexAD87UrFw42a-u3rxfSJkHO_s_Nlw8QD6fB3W0Oa' //live
//client_id='AermcX6XDUeE3hijPsufhfHFtz1hiS7gDHCl26MhZvqpcJy1cBNpjcQwlmlGFLdHsVxMnQ5b6rCjSWfe' //sandbox
//client_id="sb"
//"https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID"
success_purchase_json_sample={"create_time":"2021-03-05T13:46:43Z","update_time":"2021-03-05T13:48:29Z","id":"5VR35026JD8810941","intent":"CAPTURE","status":"COMPLETED","payer":{"email_address":"hmghaly@gmail.com","payer_id":"PHRMZDXHQEEVY","address":{"address_line_1":"10505 69th Ave ","address_line_2":"Apt 114","admin_area_2":"Forest Hills","admin_area_1":"NY","postal_code":"11375","country_code":"US"},"name":{"given_name":"Hussein","surname":"Ghaly"},"phone":{"phone_number":{"national_number":"3472824298"}}},"purchase_units":[{"reference_id":"default","soft_descriptor":"PAYPAL *PYPLTEST","amount":{"value":"1.00","currency_code":"USD"},"payee":{"email_address":"barco.03-facilitator@gmail.com","merchant_id":"YQZCHTGHUK5P8"},"shipping":{"name":{"full_name":"Hussein Ghaly"},"address":{"address_line_1":"10505 69th Ave ","address_line_2":"Apt 114","admin_area_2":"Forest Hills","admin_area_1":"NY","postal_code":"11375","country_code":"US"}},"payments":{"captures":[{"status":"COMPLETED","id":"2C578972UG0456027","final_capture":true,"create_time":"2021-03-05T13:48:29Z","update_time":"2021-03-05T13:48:29Z","amount":{"value":"1.00","currency_code":"USD"},"seller_protection":{"status":"ELIGIBLE","dispute_categories":["ITEM_NOT_RECEIVED","UNAUTHORIZED_TRANSACTION"]},"links":[{"href":"https://api.sandbox.paypal.com/v2/payments/captures/2C578972UG0456027","rel":"self","method":"GET","title":"GET"},{"href":"https://api.sandbox.paypal.com/v2/payments/captures/2C578972UG0456027/refund","rel":"refund","method":"POST","title":"POST"},{"href":"https://api.sandbox.paypal.com/v2/checkout/orders/5VR35026JD8810941","rel":"up","method":"GET","title":"GET"}]}]}}],"links":[{"href":"https://api.sandbox.paypal.com/v2/checkout/orders/5VR35026JD8810941","rel":"self","method":"GET","title":"GET"}]}


success_subscription_json_sample={"orderID":"7SJ6078899125653X","paymentID":null,"billingToken":"BA-89079956727979717","subscriptionID":"I-9MGJSLM3NNU5","facilitatorAccessToken":"A21AAMtD67GpVRQ828Fi6r3qmRHsH_o9gEkHiNsp0hz1vnStLi8XT3lwMrSDPYekbs7UXDAC6-wpnjgyUoN8JP6Jyf5j3scAA"}

function render_paypal_subscription_div(plan_id,div_id,callback_fn=function(){}){
    document.getElementById(div_id).innerHTML=""
    script_src="https://www.paypal.com/sdk/js?client-id=__client_id__&vault=true&intent=subscription".replace("__client_id__",client_id)
    document.getElementById("paypal_src").src=script_src //paypal script must have an ID paypal_src
      paypal.Buttons({
          style: {
              shape: 'pill',
              color: 'gold',
              layout: 'vertical',
              label: 'subscribe'
          },
          createSubscription: function(data, actions) {
            return actions.subscription.create({
              'plan_id': plan_id //'P-2E402136PT005013YMA7224A'
            });
          },
          onApprove: function(data, actions) {
            alert("transaction successful - ID: "+data.subscriptionID);
            callback_fn(data)
          }
      }).render('#'+div_id);    
}

function render_paypal_purchase_div(amount,div_id,callback_fn=function(){}){
    //client_id='ASancjQ-2tyudQRbadiBiox1Ul8LmZr0nXQwCCDexAD87UrFw42a-u3rxfSJkHO_s_Nlw8QD6fB3W0Oa'
    document.getElementById(div_id).innerHTML=""
    script_src="https://www.paypal.com/sdk/js?client-id=__client_id__".replace("__client_id__",client_id)
    document.getElementById("paypal_src").src=script_src //paypal script must have an ID paypal_src
 paypal.Buttons({
    createOrder: function(data, actions) {
      // This function sets up the details of the transaction, including the amount and line item details.
      return actions.order.create({
        purchase_units: [{
          amount: {
            value: amount.toString()
          }
        }]
      });
    },
    onApprove: function(data, actions) {
      // This function captures the funds from the transaction.
      return actions.order.capture().then(function(details) {
        // This function shows a transaction success message to your buyer.
        alert('Transaction completed by ' + details.payer.name.given_name);
          callback_fn(details)
      });
    }
  }).render('#'+div_id);

}