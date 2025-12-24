import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def ask_gpt(prompt, model=None, api_key=None, base_url=None):
    if model is None:
        model = os.getenv('MODEL', 'gemini-2.0-flash-exp')
    
    if api_key is None:
        api_key = os.getenv('API_KEY')
        
    if base_url is None:
        base_url = os.getenv('BASE_URL')

    messages = [
        {"role": "user", "content": prompt},
    ]
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ 请求失败！请检查以下配置：")
        print(f"API Key: {api_key}")
        print(f"Base URL: {base_url}")
        print(f"Model: {model}")
        print(f"错误信息: {str(e)}")
        raise e

# test
if __name__ == '__main__':
    print(ask_gpt('hi there'))