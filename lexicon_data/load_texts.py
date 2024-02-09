import aiofiles
import json
from async_lru import alru_cache

@alru_cache(maxsize=1000)
async def handlers_text(language_type: str, command: str) -> str:
    async with aiofiles.open(file='lexicon_data/lexicon.json',mode='r',encoding='utf-8') as file:
        data = await file.read()
        text_data = json.loads(data)
        try:
            res =  text_data[language_type][command]
        except KeyError:
            res =  text_data['en'][command]
        return res
