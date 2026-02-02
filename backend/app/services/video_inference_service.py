"""
Video Inference Service
Process video: extract audio -> transcribe -> diarize -> create transcript -> generate minutes -> PDF
"""
import logging
import tempfile
import httpx
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.services import audio_processing, vnpt_stt_service, diarization_service, transcript_service
from app.services import minutes_service
from app.schemas.transcript import TranscriptChunkCreate

logger = logging.getLogger(__name__)


async def process_meeting_video(
    db: Session,
    meeting_id: str,
    video_url: str,
    template_id: Optional[str] = None,
) -> dict:
    """
    Process video file through full pipeline:
    1. Download video (if URL)
    2. Extract audio
    3. Transcribe with VNPT STT
    4. Diarize speakers
    5. Create transcript chunks
    6. Generate meeting minutes
    7. Export PDF (optional)
    
    Args:
        db: Database session
        meeting_id: Meeting ID
        video_url: URL or local path to video file
        template_id: Optional template ID for minutes generation
        
    Returns:
        dict with status, transcript_count, minutes_id, pdf_url (if generated)
    """
    video_path = None
    audio_path = None
    
    try:
        # Step 1: Download video if it's a URL
        if video_url.startswith("http://") or video_url.startswith("https://"):
            logger.info(f"Downloading video from {video_url}")
            video_path = await _download_video(video_url, meeting_id)
        elif video_url.startswith("/files/"):
            # Local file path
            base_dir = Path(__file__).parent.parent.parent
            video_path = base_dir / video_url.lstrip("/")
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
        else:
            video_path = Path(video_url)
            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(f"Processing video: {video_path}")
        
        # Step 2: Extract audio
        logger.info("Extracting audio from video...")
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / f"audio_{meeting_id}.wav"
            audio_path = audio_processing.extract_audio_from_video(
                video_path,
                output_path=audio_path,
                sample_rate=16000,
                channels=1,
            )
            logger.info(f"Audio extracted: {audio_path}")
            
            # Step 3: Transcribe with VNPT STT
            logger.info("Transcribing audio with VNPT STT...")
            transcription_result = await vnpt_stt_service.transcribe_audio_file(
                audio_path,
                language_code="vi-VN",
                enable_word_time_offsets=True,
            )
            logger.info(f"Transcription completed: {len(transcription_result.segments)} segments")
            
            # Step 4: Diarize speakers
            logger.info("Diarizing speakers...")
            diarization_segments = await diarization_service.diarize_audio(audio_path)
            logger.info(f"Diarization completed: {len(diarization_segments)} segments")
            
            # Step 5: Merge transcription and diarization
            logger.info("Merging transcription and diarization...")
            merged_chunks = _merge_transcription_and_diarization(
                transcription_result.segments,
                diarization_segments,
            )
            logger.info(f"Merged into {len(merged_chunks)} chunks")
            
            # Step 6: Create transcript chunks in database
            logger.info("Saving transcript chunks to database...")
            chunks_to_create = []
            for idx, chunk in enumerate(merged_chunks, start=1):
                chunks_to_create.append(TranscriptChunkCreate(
                    meeting_id=meeting_id,
                    chunk_index=idx,
                    start_time=chunk["start_time"],
                    end_time=chunk["end_time"],
                    speaker=chunk.get("speaker", "UNKNOWN"),
                    text=chunk["text"],
                    confidence=chunk.get("confidence", 1.0),
                    language=transcription_result.language,
                ))
            
            result = transcript_service.create_batch_transcript_chunks(
                db=db,
                meeting_id=meeting_id,
                chunks=chunks_to_create,
            )
            logger.info(f"Saved {result.total} transcript chunks")
            
            # Step 7: Generate meeting minutes
            minutes_id = None
            pdf_url = None
            if template_id:
                logger.info(f"Generating meeting minutes with template {template_id}...")
                try:
                    from app.schemas.minutes import GenerateMinutesRequest
                    minutes_result = await minutes_service.generate_minutes_with_ai(
                        db=db,
                        request=GenerateMinutesRequest(
                            meeting_id=meeting_id,
                            template_id=template_id,
                            include_transcript=True,
                            include_actions=True,
                            include_decisions=True,
                            include_risks=True,
                            format="markdown",
                        ),
                    )
                    minutes_id = minutes_result.id if hasattr(minutes_result, 'id') else None
                    logger.info(f"Minutes generated: {minutes_id}")
                    
                    # TODO: Generate PDF export
                    # pdf_url = await _generate_pdf(minutes_result, meeting_id)
                    
                except Exception as e:
                    logger.error(f"Failed to generate minutes: {e}", exc_info=True)
                    # Don't fail the whole process if minutes generation fails
            
            return {
                "status": "completed",
                "transcript_count": result.total,
                "minutes_id": minutes_id,
                "pdf_url": pdf_url,
            }
            
    except Exception as e:
        logger.error(f"Video processing failed: {e}", exc_info=True)
        raise
    finally:
        # Cleanup temporary files
        if video_path and video_path != Path(video_url) and video_path.exists():
            try:
                if video_path.parent.name.startswith("tmp"):
                    video_path.unlink()
            except Exception:
                pass


async def _download_video(url: str, meeting_id: str) -> Path:
    """Download video file from URL to temporary location"""
    temp_dir = Path(tempfile.gettempdir())
    video_path = temp_dir / f"video_{meeting_id}_{Path(url).stem}.mp4"
    
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
        response = await client.get(url)
        response.raise_for_status()
        video_path.write_bytes(response.content)
    
    logger.info(f"Video downloaded to {video_path}")
    return video_path


def _merge_transcription_and_diarization(
    transcription_segments: list,
    diarization_segments: list,
) -> list:
    """
    Merge transcription segments with diarization segments to assign speakers.
    
    Args:
        transcription_segments: List of transcription segments with time_start, time_end, text
        diarization_segments: List of diarization segments with speaker, start, end
        
    Returns:
        List of merged chunks with speaker, text, time_start, time_end
    """
    merged = []
    
    # Create a mapping from time to speaker
    speaker_map = []
    for diar_seg in diarization_segments:
        speaker_map.append({
            "speaker": diar_seg["speaker"],
            "start": diar_seg["start"],
            "end": diar_seg["end"],
        })
    speaker_map.sort(key=lambda x: x["start"])
    
    # Assign speakers to transcription segments
    for trans_seg in transcription_segments:
        seg_start = trans_seg.get("time_start") or 0.0
        seg_end = trans_seg.get("time_end") or seg_start + 1.0
        seg_text = trans_seg.get("text", "")
        seg_confidence = trans_seg.get("confidence", 1.0)
        
        # Find overlapping diarization segment
        speaker = "UNKNOWN"
        for diar_seg in speaker_map:
            # Check if transcription segment overlaps with diarization segment
            if seg_start >= diar_seg["start"] and seg_start < diar_seg["end"]:
                speaker = diar_seg["speaker"]
                break
            elif seg_end > diar_seg["start"] and seg_end <= diar_seg["end"]:
                speaker = diar_seg["speaker"]
                break
            elif seg_start <= diar_seg["start"] and seg_end >= diar_seg["end"]:
                speaker = diar_seg["speaker"]
                break
        
        merged.append({
            "text": seg_text,
            "speaker": speaker,
            "start_time": seg_start,
            "end_time": seg_end,
            "confidence": seg_confidence,
        })
    
    return merged

