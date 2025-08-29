from aiohttp import ClientSession
import humanize
import datetime


def get_all_subclasses(cls) -> list:
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses.extend(get_all_subclasses(subclass))
    return subclasses


def convert_time_to_readable(seconds: int) -> str:
    humanize.i18n.activate("ru_RU")
    return humanize.naturaldelta(datetime.timedelta(seconds=seconds))


async def convert_crypto_to_rub(currency_name: str, amount: int | float) -> int | float:
    async with ClientSession() as session:
        response = await session.get(f"https://api.heleket.com/v1/exchange-rate/{currency_name}/list")
        data = await response.json()

    for result in data["result"]:
        if result["to"] == "RUB":
            return round(amount / float(result["course"]), 6)
        