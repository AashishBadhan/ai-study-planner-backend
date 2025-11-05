"""
Study Timer Service
Implements Pomodoro technique with configurable work/break intervals
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.schemas import TimerConfig, TimerState
from ..config import settings

logger = logging.getLogger(__name__)


class StudyTimerService:
    """Service for managing study timer sessions"""
    
    def __init__(self):
        """Initialize timer service"""
        self.active_timers: Dict[str, TimerState] = {}
        self.timer_configs: Dict[str, TimerConfig] = {}
    
    async def create_timer(
        self, 
        user_id: str, 
        config: Optional[TimerConfig] = None
    ) -> TimerState:
        """
        Create a new timer for a user
        
        Args:
            user_id: Unique user identifier
            config: Timer configuration (uses defaults if None)
            
        Returns:
            Initial timer state
        """
        if config is None:
            config = TimerConfig(
                study_duration=settings.DEFAULT_STUDY_DURATION,
                break_duration=settings.DEFAULT_BREAK_DURATION,
                long_break_duration=settings.DEFAULT_LONG_BREAK_DURATION,
                sessions_until_long_break=settings.POMODOROS_UNTIL_LONG_BREAK
            )
        
        self.timer_configs[user_id] = config
        
        state = TimerState(
            is_running=False,
            is_break=False,
            current_session=0,
            time_remaining=config.study_duration * 60,  # Convert to seconds
            topic=None
        )
        
        self.active_timers[user_id] = state
        logger.info(f"Created timer for user {user_id}")
        
        return state
    
    async def start_timer(
        self, 
        user_id: str, 
        topic: Optional[str] = None
    ) -> TimerState:
        """
        Start or resume the timer
        
        Args:
            user_id: User identifier
            topic: Optional topic being studied
            
        Returns:
            Updated timer state
        """
        if user_id not in self.active_timers:
            await self.create_timer(user_id)
        
        state = self.active_timers[user_id]
        config = self.timer_configs[user_id]
        
        # Start new session if timer is at 0
        if state.time_remaining == 0:
            if state.is_break:
                # Break ended, start new study session
                state.is_break = False
                state.current_session += 1
                state.time_remaining = config.study_duration * 60
            else:
                # Study session ended, start break
                state.is_break = True
                
                # Determine break type (short or long)
                if state.current_session % config.sessions_until_long_break == 0:
                    state.time_remaining = config.long_break_duration * 60
                else:
                    state.time_remaining = config.break_duration * 60
        
        state.is_running = True
        if topic:
            state.topic = topic
        
        logger.info(f"Timer started for user {user_id}, session {state.current_session}")
        return state
    
    async def pause_timer(self, user_id: str) -> TimerState:
        """Pause the timer"""
        if user_id in self.active_timers:
            self.active_timers[user_id].is_running = False
            logger.info(f"Timer paused for user {user_id}")
        return self.active_timers.get(user_id)
    
    async def reset_timer(self, user_id: str) -> TimerState:
        """Reset timer to initial state"""
        if user_id in self.active_timers:
            config = self.timer_configs[user_id]
            self.active_timers[user_id] = TimerState(
                is_running=False,
                is_break=False,
                current_session=0,
                time_remaining=config.study_duration * 60,
                topic=None
            )
            logger.info(f"Timer reset for user {user_id}")
        return self.active_timers.get(user_id)
    
    async def get_timer_state(self, user_id: str) -> Optional[TimerState]:
        """Get current timer state"""
        return self.active_timers.get(user_id)
    
    async def update_timer(self, user_id: str, elapsed_seconds: int) -> TimerState:
        """
        Update timer after elapsed time
        
        Args:
            user_id: User identifier
            elapsed_seconds: Seconds elapsed since last update
            
        Returns:
            Updated timer state
        """
        if user_id not in self.active_timers:
            return None
        
        state = self.active_timers[user_id]
        
        if state.is_running:
            state.time_remaining = max(0, state.time_remaining - elapsed_seconds)
        
        return state
    
    def format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    async def get_notification_message(self, user_id: str) -> Optional[str]:
        """
        Get notification message if timer completed
        
        Returns:
            Notification message or None
        """
        if user_id not in self.active_timers:
            return None
        
        state = self.active_timers[user_id]
        
        if state.time_remaining == 0:
            if state.is_break:
                return "Break time is over! Ready to study?"
            else:
                config = self.timer_configs[user_id]
                if state.current_session % config.sessions_until_long_break == 0:
                    return f"Great work! Take a {config.long_break_duration} minute break."
                else:
                    return f"Session complete! Take a {config.break_duration} minute break."
        
        return None
    
    async def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for the current timer session
        
        Returns:
            Dictionary with session statistics
        """
        if user_id not in self.active_timers:
            return {}
        
        state = self.active_timers[user_id]
        config = self.timer_configs[user_id]
        
        total_study_time = state.current_session * config.study_duration
        total_break_time = (state.current_session // config.sessions_until_long_break) * config.long_break_duration
        total_break_time += (state.current_session % config.sessions_until_long_break) * config.break_duration
        
        return {
            'sessions_completed': state.current_session,
            'total_study_minutes': total_study_time,
            'total_break_minutes': total_break_time,
            'current_topic': state.topic,
            'is_break': state.is_break,
            'time_remaining': self.format_time(state.time_remaining)
        }


# Singleton instance
timer_service = StudyTimerService()
