from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.isbp_client import IsbpClientError
from app.services.isbp_service import IsbpIntegrationService


logger = logging.getLogger(__name__)


async def main_async(limit: int | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async with AsyncSessionLocal() as session:
        search_paths = [
            schema
            for schema in [settings.DB_SCHEMA_PUBLIC, settings.DB_SCHEMA_REMOTE]
            if schema
        ]
        if search_paths:
            await session.execute(text(f"SET search_path TO {', '.join(search_paths)}"))

        targets = await IsbpIntegrationService.collect_pending_poll_targets(
            session,
            limit=limit or settings.ISBP_POLL_LIMIT,
        )

        if not targets:
            logger.info("No pending ISBP incidents to poll.")
            return

        logger.inюfo("Polling %s pending ISBP incident(s).", len(targets))
        for target in targets:
            try:
                response = await IsbpIntegrationService.check_incident_status(
                    session,
                    mh_rn=target.mh_rn,
                    diagnosis_state_id=target.diagnosis_state_id,
                )
            except IsbpClientError as error:
                logger.warning(
                    "ISBP status check failed for diagnosis_state_id=%s: %s",
                    target.diagnosis_state_id,
                    error,
                )
                continue

            logger.info(
                "ISBP status for diagnosis_state_id=%s: %s",
                target.diagnosis_state_id,
                response.status,
            )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
