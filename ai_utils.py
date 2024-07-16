import requests

cur_model="gpt-3.5-turbo"
def chat_with_chatgpt(prompt,api_key,max_tokens=100,model=cur_model):
    res = requests.post(f"https://api.openai.com/v1/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {api_key}"
          },
          json={"model": model,"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens
          }).json()
    return res#.choices[0].text


def business_ai(website_info_dict,api_key):
  final_url=website_info_dict.get("final_url","")
  title=website_info_dict.get("title","")
  description=website_info_dict.get("description","")
  keywords=website_info_dict.get("keywords","")

  prompt="""
  Given the following information, provide company name in English, company description in English, and hs-codes of the company products, in JSON format:
  url: %s
  title: %s
  description: %s
  keywords: %s
  follow this example:
  {"company_name":"Company A", "description":"our company provides these products","hs_codes":["05","09","24"]}
  """%(final_url,title,description,keywords)  
  # out=get_page_info(url,read_method="curl")
  chat_gpt_out=chat_with_chatgpt(prompt,api_key)
  out_json=chat_gpt_out["choices"][0]['message']['content']
  return json.loads(out_json)