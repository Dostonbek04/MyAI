from openai import OpenAI

client = OpenAI(api_key="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")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "hello my friend. in uzbek"},
    ],
    max_tokens=100
)

print(response.choices[0].message.content)
