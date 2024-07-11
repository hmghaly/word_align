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
