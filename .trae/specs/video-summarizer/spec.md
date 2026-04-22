# Video Summarizer - Product Requirement Document

## Overview
- **Summary**: A locally runnable video summarization system that processes YouTube URLs or local video files and generates structured summaries in Markdown format using both local and API-based LLM models.
- **Purpose**: To provide users with an easy way to extract key information from videos through automated summarization, saving time and improving content consumption efficiency.
- **Target Users**: Content consumers, researchers, students, and professionals who need to quickly understand video content without watching entire videos.

## Goals
- Build a stable, locally runnable video summarization system
- Support both YouTube URLs and local video files as input
- Generate multiple types of summaries (Markdown, section, timeline, outline)
- Support both local LLM inference (Ollama) and API-based inference (Kimi, DeepSeek)
- Provide a modular, extensible architecture with easy model switching
- Ensure reliability through intermediate file storage and retry mechanisms

## Non-Goals (Out of Scope)
- Real-time video processing
- Video editing or modification
- Support for non-English languages (initial version)
- GUI interface (command-line only)
- Cloud deployment

## Background & Context
- The system uses a linear processing pipeline: download → audio extraction → speech-to-text → text chunking → LLM summarization → output
- Each stage is independent and file-based to ensure reliability and restart capability
- The system prioritizes low hallucination risk and factual accuracy

## Functional Requirements
- **FR-1**: Download video content from YouTube URLs using yt-dlp
- **FR-2**: Extract audio from video files using ffmpeg
- **FR-3**: Transcribe audio to text using WhisperX
- **FR-4**: Split transcript into chunks for processing
- **FR-5**: Generate summaries using configurable LLM providers
- **FR-6**: Support multiple summarization strategies (map-reduce, timeline, outline)
- **FR-7**: Output summaries in Markdown format
- **FR-8**: Provide CLI interface with configurable parameters

## Non-Functional Requirements
- **NFR-1**: Reliability - system must handle errors gracefully with retry mechanisms
- **NFR-2**: Modularity - each component must be independent and replaceable
- **NFR-3**: Performance - use GPU acceleration where possible
- **NFR-4**: Extensibility - easy to add new LLM providers and summarization strategies
- **NFR-5**: Low hallucination risk - prompts must ensure factual accuracy

## Constraints
- **Technical**: Python 3.11+, requires yt-dlp, ffmpeg, WhisperX, and Ollama (for local inference)
- **Business**: No external API costs for local inference mode
- **Dependencies**: External APIs require API keys (Kimi, DeepSeek)

## Assumptions
- Users have Python 3.11+ installed
- Users have necessary system dependencies (ffmpeg) installed
- For local inference, users have Ollama and appropriate models installed
- For API-based inference, users have valid API keys

## Acceptance Criteria

### AC-1: Video Download
- **Given**: A valid YouTube URL is provided
- **When**: The system is run with the URL
- **Then**: The video is downloaded successfully
- **Verification**: `programmatic`

### AC-2: Audio Extraction and Transcription
- **Given**: A video file (local or downloaded)
- **When**: The system processes the video
- **Then**: Audio is extracted and transcribed to text with timestamps
- **Verification**: `programmatic`

### AC-3: Text Chunking
- **Given**: A transcript file
- **When**: The system processes the transcript
- **Then**: The transcript is split into chunks of configurable size
- **Verification**: `programmatic`

### AC-4: LLM Summarization
- **Given**: Text chunks and a configured LLM provider
- **When**: The system generates summaries
- **Then**: Summaries are generated according to the selected strategy
- **Verification**: `human-judgment`

### AC-5: Output Generation
- **Given**: Generated summaries
- **When**: The system completes processing
- **Then**: A Markdown file is created with structured summaries
- **Verification**: `human-judgment`

### AC-6: CLI Functionality
- **Given**: A command-line interface
- **When**: Users run the system with different parameters
- **Then**: The system responds correctly to parameter changes
- **Verification**: `programmatic`

### AC-7: LLM Provider Switching
- **Given**: Different LLM provider configurations
- **When**: The system is run with different providers
- **Then**: The system uses the specified provider for summarization
- **Verification**: `programmatic`

### AC-8: Summarization Mode Switching
- **Given**: Different summarization mode configurations
- **When**: The system is run with different modes
- **Then**: The system generates summaries according to the selected mode
- **Verification**: `human-judgment`

## Open Questions
- [ ] What are the specific hardware requirements for GPU acceleration?
- [ ] How to handle very long videos that exceed LLM context windows?
- [ ] What is the expected processing time for different video lengths?
- [ ] How to handle videos with poor audio quality or multiple speakers?