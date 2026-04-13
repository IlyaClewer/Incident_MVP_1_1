# app/workers/recalc_diagnosis_for_all_cards.py
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.cards import StacCard
from app.services.mh_rn_diagnosis.diagnosis_engine_service_mh_rn import calculate_diagnoses_for_mhrn
from app.services.mh_rn_diagnosis.diagnosis_persist_service import persist_diagnoses_for_mhrn


logger = logging.getLogger(__name__)


async def main_async(experts_group_id: int = 1) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async with AsyncSessionLocal() as session:
        # 1. Собираем все стацкарты (пока без фильтра по dischargedate)
        # Если нужно только «открытые», можно добавить:
        # .where(StacCard.daishargedate.is_(None))
        res = await session.execute(select(StacCard.mh_rn))
        mh_rns = [row[0] for row in res.all()]

    if not mh_rns:
        logger.info("No stac cards found, nothing to recalc.")
        return

    logger.info("Found %s stac cards to recalc diagnoses.", len(mh_rns))

    # 2. Идём по списку карт и считаем диагнозы для каждой
    async with AsyncSessionLocal() as session:
        for mh_rn in mh_rns:
            logger.info("Recalculating diagnoses for mh_rn=%s ...", mh_rn)

            calc_result = await calculate_diagnoses_for_mhrn(
                session,
                mh_rn=mh_rn,
                experts_group_id=experts_group_id,
            )
            await persist_diagnoses_for_mhrn(
                session,
                mh_rn=mh_rn,
                calc_result=calc_result,
                experts_group_id=experts_group_id,
            )
            # Коммитим после каждой карты, чтобы большие объёмы не висели в транзакции
            await session.commit()

            logger.info("Recalc for mh_rn=%s completed.", mh_rn)


def main() -> None:

    # На будущее можно добавить сюда парсинг experts_group_id из аргумента
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
