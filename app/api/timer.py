"""
API Routes for Study Timer (Pomodoro Technique)
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
import logging
import asyncio
import json
from ..services.timer_service import timer_service
from ..models.schemas import TimerConfig, TimerState

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create")
async def create_timer(
    user_id: str,
    study_duration: int = 25,
    break_duration: int = 5,
    long_break_duration: int = 15,
    sessions_until_long_break: int = 4
):
    """
    Create a new study timer with custom configuration
    
    Input:
    - user_id: Unique user identifier
    - study_duration: Study session length (minutes)
    - break_duration: Short break length (minutes)
    - long_break_duration: Long break length (minutes)
    - sessions_until_long_break: Number of sessions before long break
    """
    try:
        config = TimerConfig(
            study_duration=study_duration,
            break_duration=break_duration,
            long_break_duration=long_break_duration,
            sessions_until_long_break=sessions_until_long_break
        )
        
        state = await timer_service.create_timer(user_id, config)
        
        return {
            "success": True,
            "message": "Timer created successfully",
            "state": state
        }
    except Exception as e:
        logger.error(f"Timer creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_timer(user_id: str, topic: Optional[str] = None):
    """Start or resume the timer"""
    try:
        state = await timer_service.start_timer(user_id, topic)
        
        if not state:
            raise HTTPException(status_code=404, detail="Timer not found. Create one first.")
        
        return {
            "success": True,
            "message": "Timer started",
            "state": state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timer start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_timer(user_id: str):
    """Pause the timer"""
    try:
        state = await timer_service.pause_timer(user_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Timer not found")
        
        return {
            "success": True,
            "message": "Timer paused",
            "state": state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timer pause error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_timer(user_id: str):
    """Reset the timer to initial state"""
    try:
        state = await timer_service.reset_timer(user_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Timer not found")
        
        return {
            "success": True,
            "message": "Timer reset",
            "state": state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timer reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state")
async def get_timer_state(user_id: str):
    """Get current timer state"""
    try:
        state = await timer_service.get_timer_state(user_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Timer not found")
        
        notification = await timer_service.get_notification_message(user_id)
        
        return {
            "success": True,
            "state": state,
            "notification": notification
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timer state error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_timer_stats(user_id: str):
    """Get session statistics"""
    try:
        stats = await timer_service.get_session_stats(user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Timer not found")
        
        return {
            "success": True,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Timer stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{user_id}")
async def timer_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time timer updates
    Sends timer state every second
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for user {user_id}")
    
    try:
        # Ensure timer exists
        state = await timer_service.get_timer_state(user_id)
        if not state:
            await timer_service.create_timer(user_id)
        
        while True:
            # Update timer
            state = await timer_service.update_timer(user_id, 1)
            
            if state:
                # Get notification if any
                notification = await timer_service.get_notification_message(user_id)
                
                # Send state to client
                await websocket.send_json({
                    "state": {
                        "is_running": state.is_running,
                        "is_break": state.is_break,
                        "current_session": state.current_session,
                        "time_remaining": state.time_remaining,
                        "topic": state.topic
                    },
                    "notification": notification,
                    "formatted_time": timer_service.format_time(state.time_remaining)
                })
            
            # Wait 1 second
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await websocket.close()
