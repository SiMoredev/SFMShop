# Файл src/scripts/support_demo.py
import asyncio

from openai import AsyncOpenAI

from src.core.config import settings
from src.services.support_service import answer_support
from dataclasses import dataclass


@dataclass
class DemoOrder:
    id: int
    user_id: int
    status: str


class DemoOrderRepository:
    async def get_by_id(self, order_id: int):
        orders = {
            101: DemoOrder(id=101, user_id=1, status="active"),
            202: DemoOrder(id=202, user_id=2, status="active"),
        }
        return orders.get(order_id)

    
async def main():
    order_repo = DemoOrderRepository()
    async with AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        max_retries=0,
    ) as client:
        for question in [
            "Сколько занимает доставка по городу?",
            "Какой статус у моего заказа 101?",
            "Какой статус у моего заказа 202?",
            "Какой статус у моего заказа 999?",
            "Есть ли бесплатная доставка в другой город?"
        ]:
            result = await answer_support(
                question=question,
                current_user_id=1,
                order_repo=order_repo,
                client=client,
            )
            print(result.answer)


if __name__ == "__main__":
    asyncio.run(main())