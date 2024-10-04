from openai import OpenAI
client = OpenAI()


#import os
#print(os.environ['OPENAI_API_KEY'])

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. You respond with short phrases where possible."},
        {
            "role": "user",
            "content": "Explain how voice recognition works in python."
        }
    ]
)

print(completion.choices[0].message)