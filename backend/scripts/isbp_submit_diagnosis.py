from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.isbp_service import IsbpIntegrationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or send an ISBP create-incident request for a diagnosis state."
    )
    parser.add_argument("--diagnosis-state-id", type=int, required=True)
    parser.add_argument("--comment", required=True)
    parser.add_argument("--expert-id", type=int, default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the payload, do not send a request to ISBP.",
    )
    return parser


async def main_async(args: argparse.Namespace) -> int:
    async with AsyncSessionLocal() as session:
        search_paths = [
            schema
            for schema in [settings.DB_SCHEMA_PUBLIC, settings.DB_SCHEMA_REMOTE]
            if schema
        ]
        if search_paths:
            await session.execute(text(f"SET search_path TO {', '.join(search_paths)}"))

        payload = await IsbpIntegrationService.build_create_payload(
            session,
            diagnosis_state_id=args.diagnosis_state_id,
            comment=args.comment,
            expert_id=args.expert_id,
        )

        if args.dry_run:
            print(
                json.dumps(
                    payload.model_dump(mode="json", exclude_none=True),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        response = await IsbpIntegrationService.create_incident(
            session,
            diagnosis_state_id=args.diagnosis_state_id,
            comment=args.comment,
            expert_id=args.expert_id,
        )
        print(
            json.dumps(
                response.model_dump(mode="json", exclude_none=True),
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


def main() -> int:
    parser = build_parser()
    return asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
