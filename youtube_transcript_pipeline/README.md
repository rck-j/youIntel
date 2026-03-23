# YouTube Transcript Pipeline

Small package layout for pulling transcripts from YouTube with fallbacks and batch processing for the latest 5 videos per channel.

## Structure

```text
src/yt_transcripts/
  clients/
  models/
  services/
  cli.py
config/
  channels.yaml
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

Copy `.env.example` to `.env` and add your YouTube Data API key.

## Single video

```bash
PYTHONPATH=src python -m yt_transcripts.cli single "https://www.youtube.com/watch?v=_XOV3I0EVBA"
```

Enable Whisper fallback explicitly:

```bash
PYTHONPATH=src python -m yt_transcripts.cli single "https://www.youtube.com/watch?v=_XOV3I0EVBA" --enable-whisper-fallback --whisper-model tiny
```


## Build `channels.yaml` from channel names

You can generate `config/channels.yaml` directly from a list of channel names:

```bash
PYTHONPATH=src python scripts/build_channels_yaml.py \
  --channel-name "Google for Developers" \
  --channel-name "Marques Brownlee" \
  --output config/channels.yaml
```

Or pass a text file with one channel name per line:

```bash
PYTHONPATH=src python scripts/build_channels_yaml.py \
  --input-file channel_names.txt \
  --output config/channels.yaml
```

The command prints unresolved channel names so you can review ambiguous or missing matches.

## Batch latest 5 videos (explicit channels)

```bash
PYTHONPATH=src python -m yt_transcripts.cli batch \
  --channel-id UC_x5XG1OV2P6uZZ5FSM9Ttw \
  --channel-id UCBJycsmduvYEL83R_U4JriQ \
  --max-videos 5 \
  --output-dir outputs
```

## Batch latest 5 videos (YAML channel config)

Create/update `config/channels.yaml`:

```yaml
version: 1
channels:
  - name: Google for Developers
    channel_id: UC_x5XG1OV2P6uZZ5FSM9Ttw
    enabled: true
```

Run configured channels:

```bash
PYTHONPATH=src python -m yt_transcripts.cli batch-from-config \
  --channels-config config/channels.yaml \
  --max-videos 5 \
  --output-dir outputs
```

This command uses `ChannelService` to load channels and `LatestVideosTranscriptService` to orchestrate retrieval for future extension points (processing, summarization, and persistence).

This writes one JSON file per video plus `batch_summary.json`.
