# AGENTS.md

## Project: YouTube Intelligence Pipeline
**Author:** Ricky Jaramillo  
**Philosophy:** Move, Minimally

---

## 1. High-Level Objective

The objective of this project is to build a scalable process for transforming YouTube content into structured, usable intelligence.

At a high level, the system should:

1. Discover relevant videos from defined sources
2. Retrieve transcript data through a resilient fallback process
3. Clean and structure content for downstream use
4. Generate summaries and extracted insights
5. Deliver outputs that support analysis, monitoring, and future productization

This project is not intended to be agent-driven. It should be designed as a **well-defined process** composed of **traditional service layers** and **orchestrated sub-processes**.

The end goal is to create a reliable foundation for a broader intelligence product that turns fragmented video content into structured knowledge.

---

## 2. System Philosophy

This project follows the **Move, Minimally** principle:

- Reduce manual effort wherever possible
- Favor clear process design over unnecessary abstraction
- Build modular services with explicit responsibilities
- Design for maintainability and scale from the start
- Optimize for fast validation without sacrificing long-term structure

The system should behave like a dependable pipeline, not an autonomous actor.

---

## 3. Solution Design Approach

The solution should use a **process-oriented architecture**.

### 3.1 Design Principles

- The full solution is a **business process**
- Each major step is a **sub-process**
- Each sub-process is implemented by one or more **services**
- An **orchestration layer** coordinates execution across services
- Responsibilities should remain explicit and easy to trace
- Failures should be isolated and handled at the service level where possible

### 3.2 Architectural Style

Preferred style:

- Traditional layered design
- Service-oriented internal modules
- Clear separation of concerns
- Deterministic orchestration
- Retry/fallback handling in defined process steps

This project should avoid framing internal modules as “agents.”  
They are **services** participating in a larger orchestrated process.

---

## 4. Core End-to-End Process

The system should be thought of as one end-to-end pipeline made up of the following sub-processes:

### 4.1 Content Discovery Sub-Process
Purpose:
- Identify target channels
- Retrieve the latest videos from each source
- Normalize video metadata for downstream processing

Inputs:
- Configured list of channels, creators, or topic sources

Outputs:
- Structured collection of video records

---

### 4.2 Transcript Retrieval Sub-Process
Purpose:
- Retrieve transcript content using a resilient fallback sequence

Fallback order:
1. `youtube-transcript-api`
2. `yt-dlp` caption retrieval
3. Whisper transcription from downloaded audio

Requirements:
- Each method should be encapsulated behind a service boundary
- Failures should be logged with reason codes
- A failed transcript should not stop the full process

Outputs:
- Transcript text
- Retrieval status
- Transcript source method

Example output shape:

```json
{
  "video_id": "abc123",
  "status": "success",
  "source": "youtube_transcript_api",
  "text": "..."
}


⸻

4.3 Transcript Processing Sub-Process

Purpose:
	•	Clean transcript text
	•	Normalize formatting
	•	Chunk content if needed for downstream LLM use
	•	Attach relevant metadata

Typical tasks:
	•	Remove timing artifacts
	•	Normalize whitespace
	•	Preserve source references where helpful
	•	Produce clean text units for summarization

Outputs:
	•	Processed transcript records ready for analysis

⸻

4.4 Summarization and Enrichment Sub-Process

Purpose:
	•	Transform processed transcripts into structured intelligence

Potential functions:
	•	Summary generation
	•	Key point extraction
	•	Topic tagging
	•	Entity extraction
	•	Sentiment or stance analysis
	•	Future cross-video synthesis

Outputs:
	•	Summary artifacts
	•	Structured metadata for storage or delivery

⸻

4.5 Delivery Sub-Process

Purpose:
	•	Make processed outputs usable for downstream systems and users

Examples:
	•	CLI output
	•	JSON artifacts
	•	Database persistence
	•	API responses
	•	Dashboard feeds
	•	Newsletter or digest generation

⸻

5. Service Model

The system should use modular services with narrow, well-defined responsibilities.

5.1 Service Responsibilities

Examples of expected services:

Channel Service
	•	Manage configured channel sources
	•	Resolve channel metadata
	•	Supply channels to the discovery process

Video Discovery Service
	•	Fetch latest videos for configured sources
	•	Normalize returned metadata
	•	Prevent duplicate retrieval where possible

Transcript Service
	•	Coordinate transcript retrieval attempts
	•	Route through fallback methods
	•	Return a consistent transcript result object

Caption Retrieval Service
	•	Retrieve captions through direct transcript APIs or downloaded caption files

Audio Transcription Service
	•	Convert audio to text when captions are unavailable
	•	Encapsulate Whisper-based logic

Transcript Processing Service
	•	Clean and normalize transcript text
	•	Chunk and prepare data for summarization

Summarization Service
	•	Generate summaries and extracted insights
	•	Standardize enrichment outputs

Persistence Service
	•	Save and retrieve videos, transcripts, and summaries
	•	Support idempotent processing

Logging / Monitoring Service
	•	Capture execution details
	•	Support observability and troubleshooting

These are services, not agents.

⸻

6. Orchestration Model

The orchestration layer is responsible for coordinating services into a full business process.

Responsibilities include:
	•	Execute sub-processes in the proper order
	•	Pass outputs from one service layer to the next
	•	Handle retries and fallback sequencing
	•	Track process state
	•	Isolate failures
	•	Support batch execution

The orchestration layer should remain thin.
Business logic belongs inside services, not inside orchestration code.

Example orchestration flow:
	1.	Get configured channels
	2.	Retrieve latest videos
	3.	For each video:
	•	attempt transcript retrieval
	•	process transcript
	•	generate summary
	•	persist outputs
	4.	Emit final run results

⸻

7. Recommended Project Structure

project_root/
│
├── clients/                # External API and tool integrations
│   ├── youtube_client.py
│   ├── transcript_api_client.py
│   ├── ytdlp_client.py
│   └── whisper_client.py
│
├── models/                 # Pydantic or domain models
│   ├── video.py
│   ├── transcript.py
│   ├── summary.py
│   └── process_result.py
│
├── services/               # Business logic services
│   ├── channel_service.py
│   ├── video_discovery_service.py
│   ├── transcript_service.py
│   ├── transcript_processing_service.py
│   ├── summarization_service.py
│   └── persistence_service.py
│
├── orchestration/          # Process coordination
│   ├── pipeline_runner.py
│   └── latest_videos_workflow.py
│
├── batch/                  # Batch entry points
│   └── run_latest_videos.py
│
├── config/                 # Settings and environment configuration
│   └── settings.py
│
├── tests/                  # Unit and integration tests
├── .env
├── requirements.txt
└── AGENTS.md


⸻

8. Data Model Overview

Video

Represents a discovered YouTube video.

Suggested fields:

{
  "video_id": "abc123",
  "channel_id": "channel_1",
  "channel_name": "Example Channel",
  "title": "Example Title",
  "published_at": "2026-03-21T10:00:00Z",
  "url": "https://youtube.com/watch?v=abc123"
}

Transcript

Represents transcript retrieval and processing output.

Suggested fields:

{
  "video_id": "abc123",
  "status": "success",
  "source": "whisper",
  "raw_text": "...",
  "processed_text": "..."
}

Summary

Represents downstream structured intelligence.

Suggested fields:

{
  "video_id": "abc123",
  "summary": "...",
  "key_points": [
    "Point 1",
    "Point 2"
  ],
  "topics": [
    "AI",
    "policy"
  ]
}


⸻

9. Engineering Principles

9.1 Separation of Concerns

Each service should do one thing well.

9.2 Idempotency

The same video should not be processed multiple times unless explicitly requested.

9.3 Resilience

A single failed transcript should not fail the entire batch.

9.4 Observability

Every major process step should emit logs and status outcomes.

9.5 Determinism

The system should behave predictably and be easy to debug.

9.6 Replaceability

External integrations should be wrapped so underlying tools can be swapped later.

⸻

10. Error Handling Expectations

The system should classify failures clearly.

Examples:
	•	video_fetch_failed
	•	transcript_not_available
	•	caption_download_failed
	•	audio_download_failed
	•	whisper_transcription_failed
	•	summary_generation_failed

Failures should:
	•	be logged
	•	return structured status information
	•	avoid breaking unrelated processing work

⸻

11. Current Scope

Phase 1
	•	Retrieve latest videos from configured channels
	•	Attempt transcript retrieval with fallback methods
	•	Return or persist transcript results

Phase 2
	•	Process transcript text into normalized form
	•	Add summarization
	•	Add structured output models

Phase 3
	•	Persist outputs to a database
	•	Add scheduling and repeatable runs
	•	Add monitoring and reporting

Phase 4
	•	Add multi-video synthesis
	•	Add topic-based collections
	•	Support downstream product surfaces such as dashboards or digests

⸻

12. What This Project Is Building Toward

This pipeline is the foundation for a larger intelligence product.

Future product directions may include:
	•	topic monitoring
	•	creator collection management
	•	daily or weekly brief generation
	•	multi-source intelligence aggregation
	•	dashboards and APIs for downstream applications

The current implementation should therefore prioritize:
	•	clean service boundaries
	•	reusable models
	•	reliable orchestration
	•	incremental extensibility

⸻

13. Final Design Standard

When adding new functionality, ask:

Does this belong in a defined process step?
Can this be owned by a clear service?
Does orchestration remain simple and explicit?

If the answer is no, the design likely needs to be simplified.

⸻

14. Final Principle

Build a system of services that executes a reliable process end to end.

Do not build agents where traditional service design is clearer, simpler, and more maintainable.
