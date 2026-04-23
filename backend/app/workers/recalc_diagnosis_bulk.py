from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.diagnosis_bulk_engine_service import calculate_all_diagnoses_bulk
from app.services.mh_rn_diagnosis.diagnosis_persist_service import persist_diagnoses_for_mhrn


logger = logging.getLogger(__name__)


async def main_async() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 1. Считаем диагнозы по всем mh_rn в одну структуру
    async with AsyncSessionLocal() as session:
        logger.info("Starting bulk diagnosis calculation...")
        bulk_result = await calculate_all_diagnoses_bulk(session)

    if not bulk_result:
        logger.info("No diagnoses to recalc (empty bulk_result).")
        return

    logger.info("Got results for %s mh_rn, persisting...", len(bulk_result))

    # 2. Сохраняем результаты в diagnosis_state и diagnosis_events_state
    async with AsyncSessionLocal() as session:
        for mh_rn, calc_result in bulk_result.items():
            await persist_diagnoses_for_mhrn(
                session,
                mh_rn=mh_rn,
                calc_result=calc_result,
            )
            await session.commit()

    logger.info("Bulk diagnosis recalculation completed.")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
