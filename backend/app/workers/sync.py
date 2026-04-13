from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.sync_service import SyncService


logger = logging.getLogger(__name__)


async def main_async() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting full async sync from remote FDW...")

    async with AsyncSessionLocal() as session:
        await SyncService.run_full_sync(session, default_events_class_id=1)

    logger.info("Sync completed successfully.")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
