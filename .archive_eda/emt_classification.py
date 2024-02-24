import numpy as np
import pandas as pd
import pickle
import replicate
import asyncio
import time

emt = pd.read_csv("../data/raw/emt.csv")

msgs = emt['emt message'].dropna()[0:50].tolist()

async def make_predictions():
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(replicate.async_run(
                "meta/llama-2-7b-chat",
                input={
                    "debug": False,
                    "top_k": -1,
                    "top_p": 1,
                    "prompt": msg,
                    "temperature": 0.75,
                    "system_prompt": "You are a helpful assistant that will help identify references to animal trafficking in the given message. According to Environment and Climate Change Canada, high-risk species for the Canadian illegal market include bears (particularly black, grizzly and polar bears), cougars, geese, lynx, moose, crabs, eels (elvers), lobsters, turtles (particularly blanding’s and spotted turtles), sharks and wolves. You will identify if the message is talking about one of these animals, or its parts, like fangs, skin, or fins. Do not be fooled by animal sounding words that are not actually about animals, like 'bear market'.\n\nIf you see a reference to such an animal, or an animal part, that could be for animal trafficking, then output YES. Otherwise, or if you are unsure, output NO. Do not output anything else.",
                    "max_new_tokens": 2,
                    "min_new_tokens": -1,
                    "repetition_penalty": 1
                }
            ))
            for msg in msgs
        ]

        print(f"started at {time.strftime('%X')}")
    
    results = await asyncio.gather(*tasks)

    print(f"finished at {time.strftime('%X')}")

    return results


def make_predictions_loop():
    print(f"started at {time.strftime('%X')}")
    results = [
        replicate.run(
            "meta/llama-2-7b-chat",
            input={
                "debug": False,
                "top_k": -1,
                "top_p": 1,
                "prompt": msg,
                "temperature": 0.75,
                "system_prompt": "You are a helpful assistant that will help identify references to animal trafficking in the given message. According to Environment and Climate Change Canada, high-risk species for the Canadian illegal market include bears (particularly black, grizzly and polar bears), cougars, geese, lynx, moose, crabs, eels (elvers), lobsters, turtles (particularly blanding’s and spotted turtles), sharks and wolves. You will identify if the message is talking about one of these animals, or its parts, like fangs, skin, or fins. Do not be fooled by animal sounding words that are not actually about animals, like 'bear market'.\n\nIf you see a reference to such an animal, or an animal part, that could be for animal trafficking, then output YES. Otherwise, or if you are unsure, output NO. Do not output anything else.",
                "max_new_tokens": 2,
                "min_new_tokens": -1,
                "repetition_penalty": 1
            }
        )
        for msg in msgs
    ]

    print(f"finished at {time.strftime('%X')}")
    
    return results


print(msgs)
#print(asyncio.run(make_predictions()))
print(make_predictions_loop())