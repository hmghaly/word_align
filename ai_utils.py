import requests, json, openai, time, re, traceback, copy

cur_model="gpt-3.5-turbo"
cur_model="gpt-4o"

cur_model="gpt-4o-2024-08-06"
cur_model="gpt-4o-mini-2024-07-18"
cur_model="gpt-5-nano-2025-08-07"
#gpt-4.1-nano-2025-04-14

chatgpt_api_key="XXX"


#max_completion_tokens
# messages_list = [
#     {"role": "system", "content": "You are a helpful assistant that speaks concisely and is an expert in Python programming."},
#     {"role": "user", "content": "Explain the concept of a list comprehension in Python."}
# ]

#12 Sep 2026 - generic function for both OpenAI and deepseek APIs
def chat_with_ai(prompt,api_key,max_tokens=1000,model=cur_model,params={}):
    response_format=params.get("response_format","json_object")
    system_prompt=params.get("system_prompt")
    temperature=params.get("temperature",0.2)
    reasoning_effort_deepseek=params.get("reasoning_effort","none")
    thinking_type_deepseek=params.get("thinking_type","disabled")
    base_url=params.get("base_url","https://api.openai.com/v1") #deepseek: "https://api.deepseek.com"

    messages=[{"role": "user", "content": prompt}]
    if system_prompt!=None: messages.append({"role": "user", "content": system_prompt})
    query_json_dict={"model": model,
                     "messages":messages,
                     "max_completion_tokens": max_tokens,
                     "temperature":temperature}
    if "deepseek" in base_url.lower():
      query_json_dict["reasoning_effort"]=reasoning_effort_deepseek
      query_json_dict["thinking_type"]=thinking_type_deepseek
    for a,b in query_json_dict.items(): print(a,b) #print(query_json_dict)
    if response_format=="json_object": query_json_dict["response_format"]={ "type": response_format }
    res = requests.post(f"{base_url}/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {api_key}"
          },
          json=query_json_dict).json()
    raw_dict=copy.deepcopy(res)
    try:
      query_output=res["choices"][0]["message"]["content"]
      if response_format=="json_object":
        query_output=clean_json(query_output)
        query_output_dict=json.loads(query_output)
      res["query_output"]=query_output
    except Exception as ex: 
      
      res["error"]=str(ex)
      res["trace"]=traceback.format_exc()
      res["raw"]=raw_dict

    return res


#12 Sep 2026
def calculate_api_call_cost(api_reponse_dict,ai_model,pricing_dict):
  model_cost_dict=pricing_dict.get(ai_model)
  if model_cost_dict==None: return None
  usage=api_reponse_dict.get("usage")
  if usage==None: return None
  prompt_tokens=usage.get("prompt_tokens")
  completion_tokens=usage.get("completion_tokens")
  if completion_tokens==None or prompt_tokens==None: return None
  api_call_cost=prompt_tokens*model_cost_dict["prompt_tokens"]+completion_tokens*model_cost_dict["completion_tokens"]
  return api_call_cost




#26 Feb 2026
def chat_with_chatgpt(prompt,api_key,max_tokens=1000,model=cur_model,params={}):
    response_format=params.get("response_format","json_object")
    system_prompt=params.get("system_prompt")
    temperature=params.get("temperature",0.2)

    messages=[{"role": "user", "content": prompt}]
    if system_prompt!=None: messages.append({"role": "user", "content": system_prompt})
    query_json_dict={"model": model,"messages":messages,"max_completion_tokens": max_tokens,"temperature":temperature}
    if response_format=="json_object": query_json_dict["response_format"]={ "type": response_format }
    res = requests.post(f"https://api.openai.com/v1/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {api_key}"
          },
          json=query_json_dict).json()
    raw_dict=copy.deepcopy(res)
    try:
      query_output=res["choices"][0]["message"]["content"]
      if response_format=="json_object":
        query_output=clean_json(query_output)
        query_output_dict=json.loads(query_output)
      res["query_output"]=query_output
    except Exception as ex: 
      
      res["error"]=str(ex)
      res["trace"]=traceback.format_exc()
      res["raw"]=raw_dict

    return res

# def chat_with_chatgpt(prompt,api_key,max_tokens=1000,model=cur_model,params={}):
#     response_format=params.get("response_format","json_object")
#     res = requests.post(f"https://api.openai.com/v1/chat/completions",
#           headers = {
#               "Content-Type": "application/json",
#               "Authorization": f"Bearer {api_key}"
#           },
#           json={"model": model,
#           "messages": [{"role": "user", "content": prompt}], 
#           "max_completion_tokens": max_tokens,
#           "response_format": { "type": response_format }
#           }).json()
#     try: 
#       json_output=res["choices"][0]["message"]["content"]
#       res["json_output"]=clean_json(json_output)
#     except Exception as ex: res["error"]=str(ex)
#     return res


#Cleaning up output - utility functions
#15 June 2025
def clean_json(json_str): #clean json output from AI systems
  json_str=re.sub(r'\s//.+?\n',"\n",json_str)
  json_str=re.sub(r"/\*.+?\*/","\n",json_str)
  json_str=re.sub(r'\n\-+\n',"\n",json_str)
  return json_str



def ai_query(prompt,api_key=chatgpt_api_key,max_tokens=1000,model=cur_model):
  output=chat_with_chatgpt(prompt,api_key=api_key,max_tokens=max_tokens,model=model)
  try:
    output_msg=output["choices"][0]["message"]["content"]
    #output_msg_dict=json.loads(output_msg)
    return output_msg #output_msg_dict
  except Exception as ex:
    print(str(ex))
    return output


#client = openai.OpenAI()
#web_page_extractor - "asst_wCTV2R9HAVpOmZtPU3JmahGZ"
#page_link_identifier - "asst_oFVuaaq7Dmd1L35vCdz02bmP"
#get_hs_codes - "asst_oKfhpIBNKsgMTdrNN96hA962"
#country_iso_code_converter - "asst_TFizZrNrChd6LUxxk9lC5HOl"

# 14 June 2025
def chat_with_assistant(message_input,assistant_id, client):
  thread = client.beta.threads.create()
  thread_id = thread.id

  message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=message_input 
  )    

  run = client.beta.threads.runs.create(
      thread_id=thread_id,
      assistant_id=assistant_id
  )

  while True:
      run_status = client.beta.threads.runs.retrieve(
          thread_id=thread_id,
          run_id=run.id
      )
      if run_status.status == "completed":
          break
  messages = client.beta.threads.messages.list(thread_id=thread_id)
  assistant_response = messages.data[0].content[0].text.value
  #print(assistant_response)
  return assistant_response



def chat_with_assistant_multi(message_input_list,assistant_id, client):
  all_responses=[]
  for message_input in message_input_list:
    if message_input.strip()=="": continue #cannot be empty
    thread = client.beta.threads.create()
    thread_id = thread.id

    message = client.beta.threads.messages.create(
      thread_id=thread.id,
      role="user",
      content=message_input 
    )    

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    #print(messages)
    assistant_response = messages.data[0].content[0].text.value
    all_responses.append(assistant_response)
    time.sleep(0.25)
  #print(assistant_response)
  return all_responses  




def process_out_json(json_str): #clean and parse json output from AI systems
  json_str=clean_json(json_str)
  return json.loads(json_str)


def ai_query_multi_run(prompt,n_runs,api_key=chatgpt_api_key,max_tokens=3000,model=cur_model,combine_outcomes=True):
  all_outcomes=[]
  for run_i in range(n_runs):
    #print("run_i",run_i)
    output=ai_query(prompt,api_key=api_key,max_tokens=max_tokens,model=model)
    #print(output)
    output_dict=json.loads(output)
    all_outcomes.append(output_dict)
  if not combine_outcomes: return all_outcomes
  combined_dict={}
  for o_dict0 in all_outcomes:
    for key0,vals0 in o_dict0.items():
      combined_dict[key0]=combined_dict.get(key0,[])+vals0
  return combined_dict



#========== Generate specific prompts ===========
#23 Jan 2026
def gen_business_info_prompt(content):
  prompt="""
  we need to identify business information from  the following text extracted from a web page content:
  {%s}
  ============
  extract the following information in JSON format, exactly as it appears in the text in order to match it with the original text
  {
    "business_names": ["Abb Century Ltd"],
    "business_descriptions": ["our company is a family business"],
    "business_roles": [" manufacture","produces", "supplier","providers of transport","marketplace","venue"]
    "business_products":["apples","bananas","sheet metal"],
    "business_services":["warehousing","financing","insurance"],
    "business_phones":["+33 1234234 34","+1234 2134234"],
    "business_addresses":["213 Olive st, 1231","189 Orchard Ave, 342"]
  }
  For business role, indicate only the words exactly as they appear in the text: verbs, nouns or phrases that best represent that the company does (e.g. producer, retailer, manufacurer .. etc)
  For every piece of information, it has to be pulled exactly from the text without any paraphrasing.
  """%content
  return prompt