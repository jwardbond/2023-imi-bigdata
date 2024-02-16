import pandas as pd
import replicate

df = pd.read_csv('offenders.csv')

def sanitize_corp_name(text):
    response = replicate.run(
        "meta/llama-2-70b-chat",
        input={
            "debug": False,
            "top_k": 50,
            "top_p": 1,
            "prompt": text,
            "temperature": 1,
            "system_prompt": "You are a helpful and concise assistant. I will give you the legal name of a company. You will extract just the name of the company. You will ignore the corporation number and other extraneous information. Only output the name of the company. Do NOT output anything else. Do NOT output \"Sure\" or any other boilerplate. Be concise.\n\nEXAMPLES\nInput: Company #109811 operating as Awesome Corp.\nOutput: Awesome Corp.\n\nInput: Gong Trading Corp.\nOutput: Gong Trading Corp.",
            "max_new_tokens": 10,
            "min_new_tokens": -1
        },
    )
    full_response = ''.join(response)

    return full_response


for index, row in df.iterrows():
    print(sanitize_corp_name(row['Corporation name']))