from modols.schemas import AskBody


async def ask_get(body: AskBody):
    print(body.message)
    pass
