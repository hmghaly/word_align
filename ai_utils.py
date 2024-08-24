import requests, json

cur_model="gpt-3.5-turbo"
cur_model="gpt-4o"

cur_model="gpt-4o-2024-08-06"

def chat_with_chatgpt(prompt,api_key,max_tokens=100,model=cur_model):
    res = requests.post(f"https://api.openai.com/v1/chat/completions",
          headers = {
              "Content-Type": "application/json",
              "Authorization": f"Bearer {api_key}"
          },
          json={"model": model,
          "messages": [{"role": "user", "content": prompt}], 
          "max_tokens": max_tokens,
          "response_format": { type: "json_object" }
          }).json()
    return res#.choices[0].text


