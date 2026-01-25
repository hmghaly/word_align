import requests, json, openai, time, re

cur_model="gpt-3.5-turbo"
cur_model="gpt-4o"

cur_model="gpt-4o-2024-08-06"
cur_model="gpt-4o-mini-2024-07-18"
cur_model="gpt-5-nano-2025-08-07"
#gpt-4.1-nano-2025-04-14

chatgpt_api_key="XXX"


#max_completion_tokens

def chat_with_chatgpt(prompt,api_key,max_tokens=100,model=cur_model):
    res = requests.post(f"https://api.openai.com/v1/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {api_key}"
          },
          json={"model": model,
          "messages": [{"role": "user", "content": prompt}], 
          "max_completion_tokens": max_tokens,
          "response_format": { "type": "json_object" }
          }).json()
    return res#.choices[0].text



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


#Cleaning up output - utility functions
#15 June 2025
def clean_json(json_str): #clean json output from AI systems
  json_str=re.sub(r'\s//.+?\n',"\n",json_str)
  json_str=re.sub(r"/\*.+?\*/","\n",json_str)
  json_str=re.sub(r'\n\-+\n',"\n",json_str)
  return json_str


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