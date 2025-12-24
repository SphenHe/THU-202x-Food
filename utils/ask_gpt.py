import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def ask_gpt(prompt, model=None):
    if model is None:
        model = os.getenv('MODEL', 'gemini-2.0-flash-exp')

    messages = [
        {"role": "user", "content": prompt},
    ]
    
    try:
        client = OpenAI(
            api_key=os.getenv('API_KEY'),
            base_url=os.getenv('BASE_URL')
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ 请求失败！请检查以下配置：")
        print(f"API Key: {os.getenv('API_KEY')}")
        print(f"Base URL: {os.getenv('BASE_URL')}")
        print(f"Model: {model}")
        print(f"错误信息: {str(e)}")
        raise e

# test
if __name__ == '__main__':
    print(ask_gpt('hi there'))