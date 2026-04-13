from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.diagnosis_sync_service import DiagnosisSyncService


logger = logging.getLogger(__name__)


async def main_async() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting sync diagnosis_events_directory...")

    async with AsyncSessionLocal() as session:
        await DiagnosisSyncService.sync_diagnosis_events_directory(session)
        await session.commit()

    logger.info("Sync diagnosis_events_directory completed.")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
