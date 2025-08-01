# models.py - Data Models for Excel Interview System
"""
Data models and enums for the Excel skills assessment system.
Compatible with both interview_orchestrator.py and main.py
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import uuid

# =============================================================================
# ENUMS
# =============================================================================

class SkillCategory(Enum):
    """Excel skill categories"""
    FORMULAS = "formulas"
    DATA_MANIPULATION = "data_manipulation"
    PIVOT_TABLES = "pivot_tables"
    DATA_ANALYSIS = "data_analysis"
    DATA_VISUALIZATION = "data_visualization"
    ERROR_HANDLING = "error_handling"
    ADVANCED_FUNCTIONS = "advanced_functions"

class DifficultyLevel(Enum):
    """Question difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionType(Enum):
    """Types of interview questions"""
    FREE_TEXT = "free_text"
    FILE_UPLOAD = "file_upload"
    HYBRID = "hybrid"  # Text + File

class InterviewStatus(Enum):
    """Interview session status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Question:
    """Interview question model"""
    id: str
    text: str
    type: QuestionType
    skill_category: SkillCategory
    difficulty: DifficultyLevel
    estimated_time_minutes: int
    expected_keywords: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    scoring_criteria: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type.value if hasattr(self.type, 'value') else str(self.type),
            "skill_category": self.skill_category.value if hasattr(self.skill_category, 'value') else str(self.skill_category),
            "difficulty": self.difficulty.value if hasattr(self.difficulty, 'value') else str(self.difficulty),
            "estimated_time_minutes": self.estimated_time_minutes,
            "expected_keywords": self.expected_keywords,
            "common_mistakes": self.common_mistakes,
            "scoring_criteria": self.scoring_criteria,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

@dataclass
class UserResponse:
    """User response to a question"""
    id: str
    question_id: str
    session_id: str
    text_response: Optional[str] = None
    file_path: Optional[str] = None
    time_taken_seconds: int = 0
    confidence_level: Optional[int] = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "session_id": self.session_id,
            "text_response": self.text_response,
            "file_path": self.file_path,
            "time_taken_seconds": self.time_taken_seconds,
            "confidence_level": self.confidence_level,
            "submitted_at": self.submitted_at.isoformat() if isinstance(self.submitted_at, datetime) else self.submitted_at
        }

@dataclass
class EvaluationResult:
    """Evaluation result for a response"""
    id: str
    question_id: str
    response_id: str
    score: float
    confidence: float
    reasoning: str
    strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    keywords_found: List[str] = field(default_factory=list)
    mistakes_detected: List[str] = field(default_factory=list)
    file_analysis: Optional[Dict[str, Any]] = None
    evaluator_type: str = "claude"
    evaluation_time_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "response_id": self.response_id,
            "score": self.score,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "strengths": self.strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "keywords_found": self.keywords_found,
            "mistakes_detected": self.mistakes_detected,
            "file_analysis": self.file_analysis,
            "evaluator_type": self.evaluator_type,
            "evaluation_time_ms": self.evaluation_time_ms,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

@dataclass
class ConversationMessage:
    """Conversation message in interview"""
    id: str
    session_id: str
    speaker: str  # "interviewer" or "candidate"
    message: str
    message_type: str  # "question", "response", "feedback", "introduction", etc.
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "speaker": self.speaker,
            "message": self.message,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "metadata": self.metadata
        }

@dataclass
class InterviewSession:
    """Interview session model"""
    session_id: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    status: InterviewStatus = InterviewStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    questions_asked: List[str] = field(default_factory=list)
    evaluations: List[EvaluationResult] = field(default_factory=list)
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    skills_covered: Dict[str, int] = field(default_factory=dict)
    final_score: Optional[float] = None
    final_report: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def average_score(self) -> float:
        """Calculate average score from evaluations"""
        if not self.evaluations:
            return 0.0
        return sum(eval_result.score for eval_result in self.evaluations) / len(self.evaluations)

    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "questions_asked": self.questions_asked,
            "evaluations": [eval_result.to_dict() for eval_result in self.evaluations],
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "skills_covered": self.skills_covered,
            "final_score": self.final_score,
            "final_report": self.final_report,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "average_score": self.average_score,
            "duration_minutes": self.duration_minutes
        }

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_question(
    question_id: str,
    text: str,
    question_type: str,
    skill_category: str,
    difficulty: str,
    estimated_time: int,
    expected_keywords: List[str] = None
) -> Question:
    """Factory function to create a Question"""
    
    return Question(
        id=question_id,
        text=text,
        type=QuestionType(question_type),
        skill_category=SkillCategory(skill_category),
        difficulty=DifficultyLevel(difficulty),
        estimated_time_minutes=estimated_time,
        expected_keywords=expected_keywords or []
    )

def create_user_response(
    question_id: str,
    session_id: str,
    text_response: str = None,
    file_path: str = None,
    time_taken: int = 0,
    confidence: int = None
) -> UserResponse:
    """Factory function to create a UserResponse"""
    
    return UserResponse(
        id=str(uuid.uuid4()),
        question_id=question_id,
        session_id=session_id,
        text_response=text_response,
        file_path=file_path,
        time_taken_seconds=time_taken,
        confidence_level=confidence
    )

def create_evaluation_result(
    question_id: str,
    response_id: str,
    score: float,
    confidence: float,
    reasoning: str,
    strengths: List[str] = None,
    areas_for_improvement: List[str] = None,
    keywords_found: List[str] = None
) -> EvaluationResult:
    """Factory function to create an EvaluationResult"""
    
    return EvaluationResult(
        id=str(uuid.uuid4()),
        question_id=question_id,
        response_id=response_id,
        score=score,
        confidence=confidence,
        reasoning=reasoning,
        strengths=strengths or [],
        areas_for_improvement=areas_for_improvement or [],
        keywords_found=keywords_found or []
    )

def create_interview_session(
    session_id: str = None,
    candidate_name: str = None,
    candidate_email: str = None
) -> InterviewSession:
    """Factory function to create an InterviewSession"""
    
    return InterviewSession(
        session_id=session_id or str(uuid.uuid4()),
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        start_time=datetime.utcnow()
    )

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def dict_to_question(data: Dict[str, Any]) -> Question:
    """Convert dictionary to Question object"""
    
    return Question(
        id=data["id"],
        text=data["text"],
        type=QuestionType(data["type"]),
        skill_category=SkillCategory(data["skill_category"]),
        difficulty=DifficultyLevel(data["difficulty"]),
        estimated_time_minutes=data["estimated_time_minutes"],
        expected_keywords=data.get("expected_keywords", []),
        common_mistakes=data.get("common_mistakes", []),
        scoring_criteria=data.get("scoring_criteria", {}),
        created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow())
    )

def dict_to_evaluation_result(data: Dict[str, Any]) -> EvaluationResult:
    """Convert dictionary to EvaluationResult object"""
    
    return EvaluationResult(
        id=data["id"],
        question_id=data["question_id"],
        response_id=data["response_id"],
        score=data["score"],
        confidence=data["confidence"],
        reasoning=data["reasoning"],
        strengths=data.get("strengths", []),
        areas_for_improvement=data.get("areas_for_improvement", []),
        keywords_found=data.get("keywords_found", []),
        mistakes_detected=data.get("mistakes_detected", []),
        file_analysis=data.get("file_analysis"),
        evaluator_type=data.get("evaluator_type", "claude"),
        evaluation_time_ms=data.get("evaluation_time_ms", 0),
        created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow())
    )

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_skill_category(skill: str) -> bool:
    """Validate skill category"""
    try:
        SkillCategory(skill)
        return True
    except ValueError:
        return False

def validate_difficulty_level(difficulty: str) -> bool:
    """Validate difficulty level"""
    try:
        DifficultyLevel(difficulty)
        return True
    except ValueError:
        return False

def validate_question_type(question_type: str) -> bool:
    """Validate question type"""
    try:
        QuestionType(question_type)
        return True
    except ValueError:
        return False

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_EXPECTED_KEYWORDS = {
    SkillCategory.FORMULAS: ["VLOOKUP", "INDEX", "MATCH", "SUMIF", "COUNTIF", "IF"],
    SkillCategory.DATA_MANIPULATION: ["filter", "sort", "remove duplicates", "text to columns"],
    SkillCategory.PIVOT_TABLES: ["pivot table", "summarize", "group", "calculated field"],
    SkillCategory.DATA_ANALYSIS: ["analysis", "trend", "correlation", "statistics"],
    SkillCategory.DATA_VISUALIZATION: ["chart", "graph", "conditional formatting", "dashboard"],
    SkillCategory.ERROR_HANDLING: ["#N/A", "#REF!", "#VALUE!", "IFERROR", "debug"]
}

SKILL_CATEGORY_DISPLAY_NAMES = {
    SkillCategory.FORMULAS: "Formulas & Functions",
    SkillCategory.DATA_MANIPULATION: "Data Manipulation",
    SkillCategory.PIVOT_TABLES: "Pivot Tables",
    SkillCategory.DATA_ANALYSIS: "Data Analysis",
    SkillCategory.DATA_VISUALIZATION: "Data Visualization",
    SkillCategory.ERROR_HANDLING: "Error Handling",
    SkillCategory.ADVANCED_FUNCTIONS: "Advanced Functions"
}

DIFFICULTY_LEVEL_DISPLAY_NAMES = {
    DifficultyLevel.BEGINNER: "Beginner",
    DifficultyLevel.INTERMEDIATE: "Intermediate", 
    DifficultyLevel.ADVANCED: "Advanced"
}

QUESTION_TYPE_DISPLAY_NAMES = {
    QuestionType.FREE_TEXT: "Text Response",
    QuestionType.FILE_UPLOAD: "File Upload",
    QuestionType.HYBRID: "Text + File"
}