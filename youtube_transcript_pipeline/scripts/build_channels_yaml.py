from __future__ import annotations

import argparse
import json
from pathlib import Path

from yt_transcripts.config import configure_logging
from yt_transcripts.services.channel_config_builder_service import ChannelConfigBuilderService


def _load_channel_names(channel_names: list[str], input_file: str | None) -> list[str]:
    names = list(channel_names)
    if input_file:
        file_path = Path(input_file)
        file_names = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines()]
        names.extend(name for name in file_names if name)
    return names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build channels.yaml from a list of YouTube channel names."
    )
    parser.add_argument(
        "--channel-name",
        action="append",
        default=[],
        help="Channel name to resolve (repeat for multiple values).",
    )
    parser.add_argument(
        "--input-file",
        help="Optional text file with one channel name per line.",
    )
    parser.add_argument(
        "--output",
        default="config/channels.yaml",
        help="Output path for generated channels YAML.",
    )
    return parser


def main() -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    channel_names = _load_channel_names(args.channel_name, args.input_file)
    if not channel_names:
        parser.error("Provide at least one --channel-name or --input-file.")

    builder = ChannelConfigBuilderService()
    payload, unresolved = builder.build_config(channel_names)
    builder.write_config(payload, args.output)

    print(
        json.dumps(
            {
                "output": args.output,
                "resolved": len(payload["channels"]),
                "unresolved": unresolved,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
