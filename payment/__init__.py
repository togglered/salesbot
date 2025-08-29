from abc import abstractmethod, ABC
from yoomoney import Quickpay, Client
from aiohttp import ClientSession
import asyncio
import json
import hashlib
import base64
from datetime import datetime

from database.models import Product, User
from app_config import CONFIG
from utils import convert_crypto_to_rub, convert_time_to_readable


class PaymentMethod(ABC):
    PAYMENT_ATTMEP_DELAY = 3
    PAYMENT_ATTEMPS = 100
    @abstractmethod
    async def get_payment_message(self):
        pass
    @abstractmethod
    async def check_payment(self):
        pass


if CONFIG["DEBUG_MODE"]:
    class TestPayment(PaymentMethod):
        name = "TestPayment"
        PAYMENT_ATTMEP_DELAY = 3
        PAYMENT_ATTEMPS = 100
        def __init__(self, product: Product, user: User):
            self.product = product
            self.user = user
        async def get_payment_message(self) -> str:
            return (f"💵 Для оплаты {self.product.name}, перейдите по ссылке: https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
                    f"⏰ У Вас есть {convert_time_to_readable(self.PAYMENT_ATTEMPS * self.PAYMENT_ATTMEP_DELAY)}")
        async def check_payment(self) -> bool:
            return True

if CONFIG["USE_YOOMONEY"]:
    class YooMoney(PaymentMethod):
        name = "ЮMoney"
        client = Client(token=CONFIG["YOOMONEY_TOKEN"])
        PAYMENT_ATTMEP_DELAY = 3
        PAYMENT_ATTEMPS = 100
        def __init__(self, product: Product, user: User):
            self.product = product
            self.user = user
        async def get_payment_message(self) -> str:
            quickpay = Quickpay(
                receiver=CONFIG["YOOMONEY_WALLET"],
                quickpay_form="shop",
                targets="Sponsor this project",
                paymentType="SB",
                sum=self.product.price,
                label=f"{self.user.id}:{self.product.id}"
            )
            return (f"💵 Для оплаты {self.product.name}, перейдите по ссылке: {quickpay.base_url}\n"
                    f"⏰ У Вас есть {convert_time_to_readable(self.PAYMENT_ATTEMPS * self.PAYMENT_ATTMEP_DELAY)}")
        async def check_payment(self) -> bool:
            history = self.client.operation_history()
            for operation in history.operations:
                if operation.label == f"{self.user.id}:{self.product.id}" and operation.amount >= (self.product.price * 0.9):
                    return True
            return False
    

if CONFIG["USE_HELEKET"]:
    class Heleket(PaymentMethod):
        name = "Heleket"
        PAYMENT_ATTMEP_DELAY = 3
        PAYMENT_ATTEMPS = 1200
        def __init__(self, product: Product, user: User):
            now = datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M%S")

            self.order_id = f"{user.id}-{product.id}-{date_str}"
            self.product = product
            self.user = user
        async def get_payment_message(self) -> str:
            amount = await convert_crypto_to_rub(self.coin, self.product.price)

            payload = {
                "amount": str(amount),
                "currency": self.coin,
                "order_id": self.order_id,
                "network": self.network
            }
            json_data = json.dumps(payload)
            async with ClientSession() as session:
                sign_data = json_data.encode()
                sign = hashlib.md5(base64.b64encode(sign_data) + CONFIG["HELEKET_API_KEY"].encode()).hexdigest()
                async with session.post(
                    "https://api.heleket.com/v1/payment",
                    headers={
                        "merchant": CONFIG["HELEKET_MERCHANT_UUID"],
                        "sign": sign,
                        "Content-Type": "application/json"
                    },
                    data=json_data
                ) as response:
                    data = await response.json()

            return (f'💵 Для оплаты {self.product.name}, перейдите по ссылке: {data["result"]["url"]}\n'
                    f"⏰ У Вас есть {convert_time_to_readable(self.PAYMENT_ATTEMPS * self.PAYMENT_ATTMEP_DELAY)}")
        
        async def check_payment(self) -> bool:
            payload = {
                "order_id": self.order_id
            }
            json_data = json.dumps(payload, separators=(',', ':'))
            b64 = base64.b64encode(json_data.encode()).decode()
            raw = b64 + CONFIG["HELEKET_API_KEY"]
            sign = hashlib.md5(raw.encode()).hexdigest()
            async with ClientSession() as session:
                response = await session.post(
                    "https://api.heleket.com/v1/payment/info",
                    headers={
                        "merchant": CONFIG["HELEKET_MERCHANT_UUID"],
                        "sign": sign,
                        "Content-Type": "application/json"
                    },
                    data=json_data
                )
                data = await response.json()

            status = data["result"]["status"]

            if status == "paid":
                return True
            return False
        
        
    class USDC_Arbitrum(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDC"
        network = "arbitrum"
        name = "USDC (arbitrum)"

    class USDT_Arbitrum(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "arbitrum"
        name = "USDT (arbitrum)"

    class USDT_Avalanche(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "avalanche"
        name = "USDT (avalanche)"

    class USDC_Avalanche(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDC"
        network = "avalanche"
        name = "USDC (avalanche)"

    class BCH_BCH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "BCH"
        network = "bch"
        name = "BCH (bch)"

    class USDT_BSC(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "bsc"
        name = "USDT (bsc)"

    class DAI_BSC(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "DAI"
        network = "bsc"
        name = "DAI (bsc)"

    class USDC_BSC(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDC"
        network = "bsc"
        name = "USDC (bsc)"

    class CGPT_BSC(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "CGPT"
        network = "bsc"
        name = "CGPT (bsc)"

    class DASH_DASH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "DASH"
        network = "dash"
        name = "DASH (dash)"

    class DOGE_DOGE(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "DOGE"
        network = "doge"
        name = "DOGE (doge)"

    class SHIB_ETH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "SHIB"
        network = "eth"
        name = "SHIB (eth)"

    class VERSE_ETH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "VERSE"
        network = "eth"
        name = "VERSE (eth)"

    class USDT_ETH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "eth"
        name = "USDT (eth)"

    class USDC_ETH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDC"
        network = "eth"
        name = "USDC (eth)"

    class DAI_ETH(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "DAI"
        network = "eth"
        name = "DAI (eth)"

    class POL_Polygon(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "POL"
        network = "polygon"
        name = "POL (polygon)"

    class USDT_Polygon(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "polygon"
        name = "USDT (polygon)"

    class USDC_Polygon(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDC"
        network = "polygon"
        name = "USDC (polygon)"

    class DAI_Polygon(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "DAI"
        network = "polygon"
        name = "DAI (polygon)"

    class USDT_SOL(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "sol"
        name = "USDT (sol)"

    class SOL_SOL(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "SOL"
        network = "sol"
        name = "SOL (sol)"

    class TON_TON(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "TON"
        network = "ton"
        name = "TON (ton)"

    class HMSTR_TON(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "HMSTR"
        network = "ton"
        name = "HMSTR (ton)"

    class USDT_TON(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "ton"
        name = "USDT (ton)"

    class TRX_TRON(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "TRX"
        network = "tron"
        name = "TRX (tron)"

    class USDT_TRON(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDT"
        network = "tron"
        name = "USDT (tron)"

    class USDC_TRON(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "USDC"
        network = "tron"
        name = "USDC (tron)"

    class XMR_XMR(Heleket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        coin = "XMR"
        network = "xmr"
        name = "XMR (xmr)"