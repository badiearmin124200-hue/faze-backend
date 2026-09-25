from .config import GROUP_MUSIC_PRICE_TOMAN
from .service import (
    activate_subscription,
    create_pending_subscription,
    payment_url_for,
)


async def create_payment(
    group_id: int,
    user_id: int,
):
    order = await create_pending_subscription(
        group_id,
        user_id,
    )

    return {
        "order": order,
        "payment_url": payment_url_for(
            group_id,
            user_id,
        ),
        "price": GROUP_MUSIC_PRICE_TOMAN,
    }


async def mark_payment_paid(
    group_id: int,
    user_id: int,
    payment_ref: str | None = None,
):
    return await activate_subscription(
        group_id,
        user_id,
        payment_ref,
    )