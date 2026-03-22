# AGENTS.md

## 1. Document Purpose

This document defines the architecture, design standards, and execution model for the **YouTube Intelligence Pipeline**.

It serves as a reference for:
- System design decisions
- Service boundaries
- Process orchestration
- Engineering standards

This document enforces a **process-oriented, service-based architecture** and explicitly avoids agent-based system design.

---

## 2. System Overview

### 2.1 System Name
YouTube Intelligence Pipeline

### 2.2 Objective

The system transforms unstructured YouTube video content into structured, actionable intelligence through a deterministic, orchestrated process.

Core capabilities:

- Discover relevant video content
- Retrieve transcripts using resilient fallback methods
- Normalize and process transcript data
- Generate summaries and structured insights
- Deliver outputs for downstream consumption

---

## 3. Scope

### 3.1 In Scope

- YouTube channel-based video ingestion
- Transcript retrieval (multi-method fallback)
- Transcript normalization and processing
- LLM-based summarization and enrichment
- Batch processing workflows
- Structured output generation

### 3.2 Out of Scope (Current Phase)

- Real-time streaming ingestion
- UI/Frontend applications
- User authentication and personalization
- Multi-source ingestion beyond YouTube
- Autonomous or agent-based decision systems

---

## 4. Architectural Principles

### 4.1 Process-Oriented Design
The system is a **deterministic pipeline**, not an autonomous system.

- Defined start and end states
- Explicit step sequencing
- Predictable execution

### 4.2 Service-Oriented Implementation
Each sub-process is implemented via **modular services**.

- Services have single responsibilities
- Services are independently testable
- Services do not manage orchestration

### 4.3 Orchestration-Centric Flow
A centralized orchestration layer coordinates execution.

- No implicit service chaining
- No hidden side effects
- All flow is explicit and traceable

### 4.4 Separation of Concerns
- Clients → external integrations
- Services → business logic
- Orchestration → process coordination
- Models → data contracts

### 4.5 Resilience and Fault Isolation
- Failures are contained at the service level
- Pipeline continues where possible
- All failures return structured results

### 4.6 Idempotency
- Each video is processed once per run context
- Duplicate processing is avoided unless explicitly requested

---

## 5. High-Level Process Model

The system executes a single end-to-end process composed of sub-processes.

### 5.1 Process Flow

1. Content Discovery
2. Transcript Retrieval
3. Transcript Processing
4. Summarization & Enrichment
5. Output Delivery

Each step must:
- Accept defined inputs
- Produce structured outputs
- Handle its own failure conditions

---

## 6. Sub-Process Definitions

### 6.1 Content Discovery

**Purpose:**
Retrieve latest videos from configured sources.

**Inputs:**
- Channel list (config)

**Outputs:**
- List of video metadata objects

**Key Requirements:**
- Avoid duplicate retrieval
- Normalize metadata format

---

### 6.2 Transcript Retrieval

**Purpose:**
Obtain transcript data using a defined fallback sequence.

**Fallback Strategy:**
1. youtube-transcript-api
2. yt-dlp captions
3. Whisper transcription

**Outputs:**
```json
{
  "video_id": "...",
  "status": "success | no_transcript",
  "source": "api | ytdlp | whisper",
  "text": "..."
}

Key Requirements:
	•	Must not halt pipeline on failure
	•	Must log failure reason
	•	Must standardize output format

⸻

6.3 Transcript Processing

Purpose:
Prepare transcript text for downstream use.

Functions:
	•	Clean text
	•	Remove artifacts
	•	Normalize formatting
	•	Chunk content if needed

Outputs:
	•	Processed transcript

⸻

6.4 Summarization & Enrichment

Purpose:
Convert processed transcripts into structured intelligence.

Functions:
	•	Summarization
	•	Key point extraction
	•	Topic tagging
	•	Entity extraction (future)

Outputs:

{
  "summary": "...",
  "key_points": [],
  "topics": []
}


⸻

6.5 Output Delivery

Purpose:
Persist and/or expose results.

Targets:
	•	JSON artifacts
	•	Database
	•	CLI output
	•	Future API layer

⸻

7. Service Architecture

7.1 Service Design Rules
	•	One responsibility per service
	•	No orchestration logic inside services
	•	Stateless where possible
	•	Return structured responses
	•	No direct cross-service dependencies (use orchestration)

⸻

7.2 Core Services

ChannelService
	•	Manages configured sources

VideoDiscoveryService
	•	Retrieves videos from YouTube

TranscriptService
	•	Coordinates fallback logic

CaptionService
	•	Retrieves caption-based transcripts

TranscriptionService
	•	Handles Whisper-based transcription

TranscriptProcessingService
	•	Cleans and structures transcript text

SummarizationService
	•	Generates summaries and insights

PersistenceService
	•	Stores outputs

LoggingService
	•	Centralized logging abstraction

⸻

8. Orchestration Layer

8.1 Responsibilities
	•	Execute full pipeline
	•	Control process flow
	•	Manage retries and fallback sequencing
	•	Aggregate results
	•	Handle batch execution

8.2 Constraints
	•	Must remain thin
	•	Must not contain business logic
	•	Must not duplicate service logic

⸻

9. Data Contracts

9.1 Video Model

{
  "video_id": "...",
  "channel_id": "...",
  "title": "...",
  "published_at": "...",
  "url": "..."
}

9.2 Transcript Model

{
  "video_id": "...",
  "status": "...",
  "source": "...",
  "raw_text": "...",
  "processed_text": "..."
}

9.3 Summary Model

{
  "video_id": "...",
  "summary": "...",
  "key_points": [],
  "topics": []
}


⸻

10. Error Handling Strategy

10.1 Error Classification

Errors must be categorized:
	•	discovery_failed
	•	transcript_not_available
	•	caption_fetch_failed
	•	audio_download_failed
	•	transcription_failed
	•	processing_failed
	•	summarization_failed

10.2 Handling Rules
	•	Errors must not crash the pipeline
	•	Errors must be logged with context
	•	Errors must return structured responses

⸻

11. Observability

11.1 Logging Requirements

Each step must log:
	•	Input identifiers (video_id)
	•	Execution status
	•	Duration
	•	Failure reason (if applicable)

11.2 Metrics (Future)
	•	Transcript success rate
	•	Source distribution (API vs Whisper)
	•	Processing time per stage
	•	Failure rates by category

⸻

12. Project Structure Standard

project_root/
│
├── clients/            # External integrations
├── models/             # Data contracts
├── services/           # Business logic
├── orchestration/      # Process coordination
├── batch/              # Entry points
├── config/             # Settings
├── tests/              # Test suites
│
├── .env
├── requirements.txt
└── AGENTS.md


⸻

13. Non-Functional Requirements

13.1 Performance
	•	Must support batch processing across multiple channels
	•	Must scale horizontally with workload

13.2 Reliability
	•	Pipeline must complete even with partial failures

13.3 Maintainability
	•	Clear service boundaries
	•	Minimal coupling
	•	Easy to extend

13.4 Extensibility
	•	Ability to add new transcript methods
	•	Ability to add new enrichment steps
	•	Ability to add new content sources

⸻

14. Roadmap Alignment

Phase 1
	•	Discovery + transcript retrieval

Phase 2
	•	Processing + summarization

Phase 3
	•	Persistence + scheduling

Phase 4
	•	Multi-video synthesis
	•	API layer
	•	Dashboard integration

⸻

15. Governance Rules

15.1 Do
	•	Keep services focused and simple
	•	Keep orchestration explicit
	•	Use structured data contracts
	•	Log everything relevant

15.2 Do Not
	•	Introduce agent abstractions
	•	Hide logic inside orchestration
	•	Couple services directly
	•	Allow silent failures

⸻

16. Guiding Principle

Build a deterministic system of services that executes a reliable process end-to-end.

Clarity over cleverness. Structure over abstraction. Process over autonomy.

