import requests, json

cur_model="gpt-3.5-turbo"
cur_model="gpt-4o"

cur_model="gpt-4o-2024-08-06"
cur_model="gpt-4o-mini-2024-07-18"
#gpt-4.1-nano-2025-04-14

chatgpt_api_key="XXX"


def chat_with_chatgpt(prompt,api_key,max_tokens=100,model=cur_model):
    res = requests.post(f"https://api.openai.com/v1/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {api_key}"
          },
          json={"model": model,
          "messages": [{"role": "user", "content": prompt}], 
          "max_tokens": max_tokens,
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



#web_page_extractor - "asst_wCTV2R9HAVpOmZtPU3JmahGZ"
#page_link_identifier - "asst_oFVuaaq7Dmd1L35vCdz02bmP"
#get_hs_codes - "asst_oKfhpIBNKsgMTdrNN96hA962"
#country_iso_code_converter - "asst_TFizZrNrChd6LUxxk9lC5HOl"

# 14 June 2025
def chat_with_assistant(message_input,assistant_id):
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