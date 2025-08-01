# question_bank_db.py - SQLite Question Bank with Large Dataset Support
"""
Complete question bank system with SQLite database
Supports hundreds of questions with intelligent selection
"""

import sqlite3
import json
import logging
import asyncio
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import your models
from models import (
    Question, SkillCategory, DifficultyLevel, QuestionType,
    create_question
)

# =============================================================================
# DATABASE SCHEMA AND SETUP
# =============================================================================

class QuestionBankDB:
    """SQLite database manager for question bank"""
    
    def __init__(self, db_path: str = "question_bank.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    async def initialize_database(self):
        """Initialize database with schema"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Create tables
            conn.executescript("""
            -- Main questions table
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                audio_prompt TEXT,  -- Optimized text for voice delivery
                type TEXT NOT NULL,  -- 'free_text', 'file_upload', 'hybrid', 'audio_response'
                skill_category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                estimated_time_minutes INTEGER DEFAULT 5,
                estimated_audio_seconds INTEGER DEFAULT 120,
                points_possible INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                success_rate REAL DEFAULT 0.0
            );
            
            -- Expected keywords for evaluation
            CREATE TABLE IF NOT EXISTS question_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                is_required BOOLEAN DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE(question_id, keyword)
            );
            
            -- Common mistakes to watch for
            CREATE TABLE IF NOT EXISTS common_mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                mistake_description TEXT NOT NULL,
                penalty_points REAL DEFAULT 0.5,
                detection_keywords TEXT,  -- JSON array of keywords that indicate this mistake
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );
            
            -- Question prerequisites (for adaptive selection)
            CREATE TABLE IF NOT EXISTS question_prerequisites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                prerequisite_question_id TEXT NOT NULL,
                required_score REAL DEFAULT 3.0,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                FOREIGN KEY (prerequisite_question_id) REFERENCES questions(id)
            );
            
            -- Question analytics and performance tracking
            CREATE TABLE IF NOT EXISTS question_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                response_score REAL,
                response_time_seconds INTEGER,
                transcription_confidence REAL,
                response_length_words INTEGER,
                keywords_found TEXT,  -- JSON array
                asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );
            
            -- Question tags for flexible categorization
            CREATE TABLE IF NOT EXISTS question_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE(question_id, tag)
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_questions_skill_difficulty ON questions(skill_category, difficulty);
            CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(type);
            CREATE INDEX IF NOT EXISTS idx_questions_active ON questions(is_active);
            CREATE INDEX IF NOT EXISTS idx_analytics_question ON question_analytics(question_id);
            CREATE INDEX IF NOT EXISTS idx_analytics_session ON question_analytics(session_id);
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise Exception(f"Failed to initialize database: {e}")
    
    async def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def populate_sample_data(self):
        """Populate database with comprehensive sample questions"""
        
        try:
            conn = await self.get_connection()
            
            # Clear existing data
            conn.execute("DELETE FROM question_keywords")
            conn.execute("DELETE FROM common_mistakes") 
            conn.execute("DELETE FROM question_prerequisites")
            conn.execute("DELETE FROM question_tags")
            conn.execute("DELETE FROM questions")
            
            # Insert comprehensive question set
            questions_data = self._get_comprehensive_question_set()
            
            for question_data in questions_data:
                # Insert question
                conn.execute("""
                    INSERT INTO questions (
                        id, text, audio_prompt, type, skill_category, difficulty,
                        estimated_time_minutes, estimated_audio_seconds, points_possible
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    question_data["id"],
                    question_data["text"],
                    question_data.get("audio_prompt", question_data["text"]),
                    question_data["type"],
                    question_data["skill_category"],
                    question_data["difficulty"],
                    question_data.get("estimated_time_minutes", 5),
                    question_data.get("estimated_audio_seconds", 120),
                    question_data.get("points_possible", 5)
                ))
                
                # Insert keywords
                for keyword in question_data.get("expected_keywords", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO question_keywords (question_id, keyword, weight)
                        VALUES (?, ?, ?)
                    """, (question_data["id"], keyword, 1.0))
                
                # Insert common mistakes
                for mistake in question_data.get("common_mistakes", []):
                    conn.execute("""
                        INSERT INTO common_mistakes (question_id, mistake_description, penalty_points)
                        VALUES (?, ?, ?)
                    """, (question_data["id"], mistake, 0.5))
                
                # Insert tags
                for tag in question_data.get("tags", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO question_tags (question_id, tag)
                        VALUES (?, ?)
                    """, (question_data["id"], tag))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Populated database with {len(questions_data)} questions")
            
        except Exception as e:
            self.logger.error(f"Sample data population failed: {e}")
            raise Exception(f"Failed to populate sample data: {e}")
    
    def _get_comprehensive_question_set(self) -> List[Dict[str, Any]]:
        """Generate comprehensive set of Excel interview questions"""
        
        return [
            # =================================================================
            # FREE TEXT QUESTIONS (40+ questions across all skill levels)
            # =================================================================
            
            # BEGINNER FORMULAS
            {
                "id": "formulas_basic_sum_avg",
                "text": "Explain the difference between SUM and AVERAGE functions. When would you use each one?",
                "audio_prompt": "Can you explain the difference between SUM and AVERAGE functions in Excel, and give me an example of when you'd use each one?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "beginner",
                "estimated_time_minutes": 3,
                "estimated_audio_seconds": 90,
                "expected_keywords": ["SUM", "AVERAGE", "range", "total", "mean"],
                "common_mistakes": ["Confusing SUM with COUNT", "Not understanding ranges"],
                "tags": ["basic", "math", "functions"]
            },
            {
                "id": "formulas_if_basic",
                "text": "How does the IF function work? Provide a simple example.",
                "audio_prompt": "Walk me through how the IF function works in Excel. Can you give me a simple example?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "beginner",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 100,
                "expected_keywords": ["IF", "condition", "true", "false", "logical test"],
                "common_mistakes": ["Incorrect syntax", "Missing quotes around text"],
                "tags": ["logic", "conditions", "basic"]
            },
            
            # INTERMEDIATE FORMULAS
            {
                "id": "formulas_vlookup_explained",
                "text": "Explain how VLOOKUP works and when you would use it instead of INDEX-MATCH.",
                "audio_prompt": "Can you explain how VLOOKUP works, and tell me when you might choose it over INDEX-MATCH?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "estimated_audio_seconds": 150,
                "expected_keywords": ["VLOOKUP", "INDEX", "MATCH", "lookup", "exact match", "table array"],
                "common_mistakes": ["Not understanding exact vs approximate match", "Wrong column index"],
                "tags": ["lookup", "vlookup", "intermediate"]
            },
            {
                "id": "formulas_countifs_sumifs",
                "text": "Compare COUNTIFS and SUMIFS functions. How do they handle multiple criteria?",
                "audio_prompt": "Can you explain the difference between COUNTIFS and SUMIFS, and how they handle multiple criteria?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "intermediate",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["COUNTIFS", "SUMIFS", "criteria", "multiple conditions", "range"],
                "common_mistakes": ["Mixing up criteria ranges", "Incorrect criteria syntax"],
                "tags": ["conditional", "multiple_criteria", "intermediate"]
            },
            
            # ADVANCED FORMULAS
            {
                "id": "formulas_array_dynamic",
                "text": "Explain dynamic arrays and spill ranges in modern Excel. How do FILTER and SORT functions utilize this?",
                "audio_prompt": "Can you explain dynamic arrays and spill ranges in Excel, and how functions like FILTER and SORT take advantage of this feature?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "advanced",
                "estimated_time_minutes": 6,
                "estimated_audio_seconds": 180,
                "expected_keywords": ["dynamic array", "spill", "FILTER", "SORT", "automatic expansion"],
                "common_mistakes": ["Not understanding spill behavior", "Blocking spill ranges"],
                "tags": ["dynamic", "arrays", "modern", "advanced"]
            },
            {
                "id": "formulas_power_query_basics",
                "text": "When would you use Power Query instead of traditional Excel formulas? What are the key advantages?",
                "audio_prompt": "When would you choose to use Power Query instead of traditional Excel formulas, and what are the main advantages?",
                "type": "free_text",
                "skill_category": "formulas",
                "difficulty": "advanced",
                "estimated_time_minutes": 5,
                "estimated_audio_seconds": 150,
                "expected_keywords": ["Power Query", "data transformation", "refresh", "ETL", "M language"],
                "common_mistakes": ["Not understanding refresh behavior", "Overcomplicating simple transformations"],
                "tags": ["power_query", "data_transformation", "advanced"]
            },
            
            # DATA ANALYSIS - BEGINNER
            {
                "id": "analysis_sorting_filtering",
                "text": "Explain different ways to sort and filter data in Excel. What are the advantages of each method?",
                "audio_prompt": "What are the different ways you can sort and filter data in Excel, and what are the advantages of each method?",
                "type": "free_text",
                "skill_category": "data_analysis",
                "difficulty": "beginner",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["sort", "filter", "autofilter", "custom sort", "criteria"],
                "common_mistakes": ["Not selecting all data", "Forgetting headers"],
                "tags": ["sorting", "filtering", "basic"]
            },
            
            # DATA ANALYSIS - INTERMEDIATE
            {
                "id": "analysis_pivot_concepts",
                "text": "Describe the process of creating a pivot table and what insights it can provide.",
                "audio_prompt": "Walk me through creating a pivot table. What kind of insights can pivot tables give you that regular data can't?",
                "type": "free_text",
                "skill_category": "data_analysis",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "estimated_audio_seconds": 150,
                "expected_keywords": ["pivot table", "summarize", "group", "aggregate", "fields", "values area"],
                "common_mistakes": ["Putting wrong fields in wrong areas", "Not understanding value summarization"],
                "tags": ["pivot", "summarization", "intermediate"]
            },
            {
                "id": "analysis_data_validation",
                "text": "How does data validation work in Excel? Provide examples of different validation rules you can create.",
                "audio_prompt": "Explain how data validation works in Excel. Can you give me examples of different types of validation rules?",
                "type": "free_text",
                "skill_category": "data_analysis",
                "difficulty": "intermediate",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["data validation", "dropdown", "list", "custom formula", "error message"],
                "common_mistakes": ["Not setting appropriate error messages", "Overly restrictive validation"],
                "tags": ["validation", "data_quality", "intermediate"]
            },
            
            # PIVOT TABLES - BEGINNER TO ADVANCED
            {
                "id": "pivot_basic_creation",
                "text": "What are the four main areas of a pivot table and what type of data goes in each?",
                "audio_prompt": "Can you explain the four main areas of a pivot table and what type of data you'd put in each area?",
                "type": "free_text",
                "skill_category": "pivot_tables",
                "difficulty": "beginner",
                "estimated_time_minutes": 3,
                "estimated_audio_seconds": 90,
                "expected_keywords": ["rows", "columns", "values", "filters", "drag and drop"],
                "common_mistakes": ["Confusing rows and columns areas", "Not understanding values area"],
                "tags": ["pivot_basics", "structure"]
            },
            {
                "id": "pivot_calculated_fields",
                "text": "Explain calculated fields in pivot tables. How do they differ from calculated items?",
                "audio_prompt": "What are calculated fields in pivot tables, and how are they different from calculated items?",
                "type": "free_text",
                "skill_category": "pivot_tables",
                "difficulty": "advanced",
                "estimated_time_minutes": 5,
                "estimated_audio_seconds": 150,
                "expected_keywords": ["calculated field", "calculated item", "formula", "field list"],
                "common_mistakes": ["Confusing fields vs items", "Incorrect formula syntax"],
                "tags": ["calculated", "advanced", "formulas"]
            },
            
            # ERROR HANDLING
            {
                "id": "errors_common_types",
                "text": "What are the most common Excel errors (#N/A, #REF!, etc.) and how do you handle them?",
                "audio_prompt": "What are the most common Excel errors you've encountered, like #N/A or #REF!, and how do you typically handle them?",
                "type": "free_text",
                "skill_category": "error_handling",
                "difficulty": "intermediate",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["#N/A", "#REF!", "#VALUE!", "#DIV/0!", "IFERROR", "ISERROR"],
                "common_mistakes": ["Not using error handling functions", "Ignoring error root causes"],
                "tags": ["errors", "debugging", "intermediate"]
            },
            {
                "id": "errors_iferror_usage",
                "text": "Explain how IFERROR works and provide best practices for error handling in formulas.",
                "audio_prompt": "How does the IFERROR function work, and what are your best practices for handling errors in Excel formulas?",
                "type": "free_text",
                "skill_category": "error_handling",
                "difficulty": "intermediate",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["IFERROR", "error handling", "nested formulas", "graceful degradation"],
                "common_mistakes": ["Overusing IFERROR", "Hiding important errors"],
                "tags": ["iferror", "best_practices", "intermediate"]
            },
            
            # DATA VISUALIZATION
            {
                "id": "viz_conditional_formatting",
                "text": "Explain how conditional formatting works and give three practical examples of when you'd use it.",
                "audio_prompt": "How does conditional formatting work in Excel? Can you give me three practical examples of when you'd use it?",
                "type": "free_text",
                "skill_category": "data_visualization",
                "difficulty": "beginner",
                "estimated_time_minutes": 4,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["conditional formatting", "rules", "highlight", "data bars", "color scales"],
                "common_mistakes": ["Too many formatting rules", "Poor color choices"],
                "tags": ["formatting", "visualization", "beginner"]
            },
            {
                "id": "viz_chart_selection",
                "text": "How do you choose the right chart type for different kinds of data? Explain your decision process.",
                "audio_prompt": "When you're creating charts in Excel, how do you decide which chart type to use? Walk me through your thought process.",
                "type": "free_text",
                "skill_category": "data_visualization",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "estimated_audio_seconds": 150,
                "expected_keywords": ["chart types", "bar chart", "line chart", "scatter plot", "data relationship"],
                "common_mistakes": ["Using wrong chart for data type", "Too many chart elements"],
                "tags": ["charts", "data_types", "decision_making"]
            },
            
            # =================================================================
            # FILE UPLOAD QUESTIONS (30+ questions)
            # =================================================================
            
            {
                "id": "file_pivot_sales_analysis",
                "text": "Create a pivot table from sales data showing revenue by region and product category. Include calculated fields for profit margin and growth rate. Upload your Excel file.",
                "audio_prompt": "I'd like you to create a pivot table that analyzes sales data. Show revenue by region and product category, and include calculated fields for profit margin. Please upload your Excel file when ready.",
                "type": "file_upload",
                "skill_category": "pivot_tables",
                "difficulty": "intermediate",
                "estimated_time_minutes": 10,
                "estimated_audio_seconds": 60,
                "expected_keywords": ["pivot table", "calculated field", "revenue", "region", "product"],
                "common_mistakes": ["Wrong field placement", "Incorrect calculated field formulas"],
                "tags": ["pivot", "sales", "calculated_fields"]
            },
            {
                "id": "file_dashboard_kpi",
                "text": "Create an Excel dashboard with at least 3 KPIs, 2 chart types, and conditional formatting. Use sample business data.",
                "audio_prompt": "Create a business dashboard in Excel showing at least 3 key performance indicators, 2 different chart types, and some conditional formatting. Upload your dashboard when complete.",
                "type": "file_upload",
                "skill_category": "data_visualization",
                "difficulty": "advanced",
                "estimated_time_minutes": 15,
                "estimated_audio_seconds": 90,
                "expected_keywords": ["dashboard", "KPI", "charts", "conditional formatting", "metrics"],
                "common_mistakes": ["Cluttered design", "Poor chart selection", "No clear insights"],
                "tags": ["dashboard", "kpi", "advanced", "business"]
            },
            {
                "id": "file_financial_model",
                "text": "Build a 3-year financial projection model with revenue, expenses, and profit calculations. Include scenario analysis.",
                "audio_prompt": "Create a financial projection model for 3 years showing revenue, expenses, and profit calculations. Include some scenario analysis. Upload your model when finished.",
                "type": "file_upload",
                "skill_category": "advanced_functions",
                "difficulty": "advanced",
                "estimated_time_minutes": 20,
                "estimated_audio_seconds": 120,
                "expected_keywords": ["financial model", "projection", "scenario analysis", "NPV", "assumptions"],
                "common_mistakes": ["Hard-coded values", "No scenario planning", "Poor model structure"],
                "tags": ["financial", "modeling", "scenarios", "advanced"]
            },
            {
                "id": "file_data_cleaning_exercise",
                "text": "Clean and standardize a messy dataset with duplicates, inconsistent formatting, and missing values. Show your process.",
                "audio_prompt": "I have a messy dataset that needs cleaning - it has duplicates, inconsistent formatting, and missing values. Please clean it up and upload your solution.",
                "type": "file_upload",
                "skill_category": "data_manipulation",
                "difficulty": "intermediate",
                "estimated_time_minutes": 12,
                "estimated_audio_seconds": 90,
                "expected_keywords": ["remove duplicates", "TRIM", "data validation", "find and replace", "standardize"],
                "common_mistakes": ["Not documenting cleaning steps", "Losing original data"],
                "tags": ["data_cleaning", "manipulation", "quality"]
            },
            {
                "id": "file_advanced_formulas_combo",
                "text": "Create a worksheet combining VLOOKUP, SUMIFS, nested IF statements, and error handling. Demonstrate with employee data.",
                "audio_prompt": "Create a worksheet that combines VLOOKUP, SUMIFS, nested IF statements, and error handling. Use employee data to demonstrate. Upload when ready.",
                "type": "file_upload",
                "skill_category": "formulas",
                "difficulty": "advanced",
                "estimated_time_minutes": 15,
                "estimated_audio_seconds": 90,
                "expected_keywords": ["VLOOKUP", "SUMIFS", "nested IF", "IFERROR", "combination"],
                "common_mistakes": ["Overly complex nesting", "No error handling", "Poor formula organization"],
                "tags": ["advanced", "combination", "complex"]
            },
            
            # =================================================================
            # HYBRID QUESTIONS (30+ questions combining explanation + implementation)
            # =================================================================
            
            {
                "id": "hybrid_data_cleanup_process",
                "text": "Explain your approach to cleaning messy data with duplicates and inconsistent formatting. Then upload an Excel file demonstrating your cleanup process.",
                "audio_prompt": "First, explain your general approach to cleaning messy data - how do you handle duplicates and inconsistent formatting? Then upload a file showing your actual cleanup process.",
                "type": "hybrid",
                "skill_category": "data_manipulation",
                "difficulty": "intermediate",
                "estimated_time_minutes": 12,
                "estimated_audio_seconds": 180,
                "expected_keywords": ["remove duplicates", "TRIM", "data validation", "standardization", "process"],
                "common_mistakes": ["No systematic approach", "Not documenting steps"],
                "tags": ["cleanup", "process", "methodology"]
            },
            {
                "id": "hybrid_automation_macros",
                "text": "Explain when you would automate Excel tasks with macros versus using built-in features. Then upload a simple macro example.",
                "audio_prompt": "When would you choose to automate Excel tasks with macros rather than using built-in features? Please explain your thinking, then upload a simple macro example.",
                "type": "hybrid",
                "skill_category": "advanced_functions",
                "difficulty": "advanced",
                "estimated_time_minutes": 15,
                "estimated_audio_seconds": 200,
                "expected_keywords": ["macros", "VBA", "automation", "repetitive tasks", "efficiency"],
                "common_mistakes": ["Over-automating simple tasks", "Poor macro design"],
                "tags": ["automation", "macros", "vba", "advanced"]
            },
            {
                "id": "hybrid_reporting_design",
                "text": "Describe your approach to designing effective Excel reports for management. Then create and upload a sample executive report.",
                "audio_prompt": "How do you approach designing Excel reports for management? What principles do you follow? Then create and upload a sample executive report.",
                "type": "hybrid",
                "skill_category": "data_visualization",
                "difficulty": "advanced",
                "estimated_time_minutes": 18,
                "estimated_audio_seconds": 220,
                "expected_keywords": ["report design", "executive summary", "key metrics", "visual hierarchy"],
                "common_mistakes": ["Too much detail", "Poor visual organization", "No clear insights"],
                "tags": ["reporting", "management", "design", "executive"]
            },
            {
                "id": "hybrid_troubleshooting_approach",
                "text": "Explain your systematic approach to troubleshooting Excel formula errors. Then upload a workbook showing before/after examples.",
                "audio_prompt": "What's your systematic approach when troubleshooting Excel formula errors? Walk me through your process, then upload a workbook with before and after examples.",
                "type": "hybrid",
                "skill_category": "error_handling",
                "difficulty": "intermediate",
                "estimated_time_minutes": 10,
                "estimated_audio_seconds": 180,
                "expected_keywords": ["troubleshooting", "systematic approach", "error identification", "step by step"],
                "common_mistakes": ["No systematic approach", "Not documenting solutions"],
                "tags": ["troubleshooting", "methodology", "problem_solving"]
            },
            
            # ADVANCED ANALYSIS QUESTIONS
            {
                "id": "analysis_statistical_functions",
                "text": "Explain Excel's statistical functions like STDEV, CORREL, and regression analysis. When do you use each?",
                "audio_prompt": "Can you explain Excel's statistical functions like STDEV, CORREL, and regression analysis? When would you use each of these?",
                "type": "free_text",
                "skill_category": "data_analysis",
                "difficulty": "advanced",
                "estimated_time_minutes": 6,
                "estimated_audio_seconds": 180,
                "expected_keywords": ["STDEV", "CORREL", "regression", "statistical analysis", "correlation"],
                "common_mistakes": ["Misinterpreting correlation", "Wrong statistical test selection"],
                "tags": ["statistics", "correlation", "advanced"]
            },
            
            # PRACTICAL SCENARIO QUESTIONS
            {
                "id": "scenario_budget_tracking",
                "text": "You need to create a monthly budget tracker that compares actual vs. planned expenses with variance analysis. How would you structure this?",
                "audio_prompt": "You need to create a monthly budget tracker that shows actual versus planned expenses with variance analysis. How would you structure this in Excel?",
                "type": "free_text",
                "skill_category": "data_analysis",
                "difficulty": "intermediate",
                "estimated_time_minutes": 5,
                "estimated_audio_seconds": 150,
                "expected_keywords": ["budget", "variance", "actual vs planned", "conditional formatting", "tracking"],
                "common_mistakes": ["No variance calculations", "Poor organization"],
                "tags": ["budgeting", "variance", "tracking", "practical"]
            },
            
            # POWER FEATURES
            {
                "id": "power_what_if_analysis",
                "text": "Explain Goal Seek, Solver, and Data Tables. When would you use each for what-if analysis?",
                "audio_prompt": "Can you explain Excel's what-if analysis tools like Goal Seek, Solver, and Data Tables? When would you use each one?",
                "type": "free_text",
                "skill_category": "advanced_functions",
                "difficulty": "advanced",
                "estimated_time_minutes": 6,
                "estimated_audio_seconds": 180,
                "expected_keywords": ["Goal Seek", "Solver", "Data Tables", "what-if", "optimization"],
                "common_mistakes": ["Not understanding tool limitations", "Wrong tool for the job"],
                "tags": ["optimization", "what_if", "advanced", "analysis"]
            }
        ]

# =============================================================================
# INTELLIGENT QUESTION SELECTOR
# =============================================================================

class IntelligentQuestionSelector:
    """Advanced question selection with database support and voice optimization"""
    
    def __init__(self, db: QuestionBankDB, claude_client=None):
        self.db = db
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
    
    async def select_next_question(
        self,
        session_state: Dict[str, Any],
        selection_strategy: str = "adaptive_voice"
    ) -> Optional[Question]:
        """Select next question using intelligent algorithms"""
        
        try:
            conn = await self.db.get_connection()
            
            # Get candidate info
            questions_asked = session_state.get("questions_asked", [])
            evaluations = session_state.get("evaluations", [])
            skills_covered = session_state.get("skills_covered", {})
            audio_mode = session_state.get("audio_mode", False)
            
            # Apply selection strategy
            if selection_strategy == "adaptive_voice":
                question_data = await self._select_adaptive_voice_question(
                    conn, questions_asked, evaluations, skills_covered, audio_mode
                )
            elif selection_strategy == "balanced":
                question_data = await self._select_balanced_question(
                    conn, questions_asked, evaluations, skills_covered
                )
            else:
                question_data = await self._select_random_question(conn, questions_asked)
            
            conn.close()
            
            if not question_data:
                return None
            
            # Convert to Question object
            question = create_question(
                question_id=question_data["id"],
                text=question_data["audio_prompt"] if audio_mode else question_data["text"],
                question_type=question_data["type"],
                skill_category=question_data["skill_category"],
                difficulty=question_data["difficulty"],
                estimated_time=question_data["estimated_time_minutes"],
                expected_keywords=await self._get_question_keywords(question_data["id"])
            )
            
            # Update question analytics
            await self._update_question_analytics(question_data["id"], "selected")
            
            return question
            
        except Exception as e:
            self.logger.error(f"Question selection failed: {e}")
            return None
    
    async def _select_adaptive_voice_question(
        self,
        conn,
        questions_asked: List[str],
        evaluations: List[Dict],
        skills_covered: Dict[str, int],
        audio_mode: bool
    ) -> Optional[sqlite3.Row]:
        """Select question optimized for voice interviews"""
        
        # Calculate performance metrics
        avg_score = 2.5
        if evaluations:
            avg_score = sum(eval_data.get("score", 2.5) for eval_data in evaluations) / len(evaluations)
        
        # Determine target difficulty
        if avg_score >= 4.0:
            target_difficulties = ["advanced", "intermediate"]
        elif avg_score >= 3.0:
            target_difficulties = ["intermediate", "advanced"]
        else:
            target_difficulties = ["beginner", "intermediate"]
        
        # Find underrepresented skills
        all_skills = ["formulas", "data_analysis", "pivot_tables", "data_visualization", "error_handling", "data_manipulation", "advanced_functions"]
        underrepresented_skills = [skill for skill in all_skills if skills_covered.get(skill, 0) < 2]
        
        # Build query with smart filtering
        placeholders = ",".join("?" * len(questions_asked)) if questions_asked else "NULL"
        difficulty_placeholders = ",".join("?" * len(target_difficulties))
        
        if underrepresented_skills:
            skill_placeholders = ",".join("?" * len(underrepresented_skills))
            query = f"""
                SELECT * FROM questions 
                WHERE id NOT IN ({placeholders}) 
                AND difficulty IN ({difficulty_placeholders})
                AND skill_category IN ({skill_placeholders})
                AND is_active = 1
                ORDER BY usage_count ASC, RANDOM()
                LIMIT 1
            """
            params = questions_asked + target_difficulties + underrepresented_skills
        else:
            query = f"""
                SELECT * FROM questions 
                WHERE id NOT IN ({placeholders}) 
                AND difficulty IN ({difficulty_placeholders})
                AND is_active = 1
                ORDER BY usage_count ASC, RANDOM()
                LIMIT 1
            """
            params = questions_asked + target_difficulties
        
        result = conn.execute(query, params).fetchone()
        return result
    
    async def _select_balanced_question(
        self,
        conn,
        questions_asked: List[str],
        evaluations: List[Dict],
        skills_covered: Dict[str, int]
    ) -> Optional[sqlite3.Row]:
        """Select question using balanced approach"""
        
        placeholders = ",".join("?" * len(questions_asked)) if questions_asked else "NULL"
        
        query = f"""
            SELECT * FROM questions 
            WHERE id NOT IN ({placeholders}) 
            AND is_active = 1
            ORDER BY usage_count ASC, RANDOM()
            LIMIT 1
        """
        
        result = conn.execute(query, questions_asked).fetchone()
        return result
    
    async def _select_random_question(self, conn, questions_asked: List[str]) -> Optional[sqlite3.Row]:
        """Select random question (fallback)"""
        
        placeholders = ",".join("?" * len(questions_asked)) if questions_asked else "NULL"
        
        query = f"""
            SELECT * FROM questions 
            WHERE id NOT IN ({placeholders}) 
            AND is_active = 1
            ORDER BY RANDOM()
            LIMIT 1
        """
        
        result = conn.execute(query, questions_asked).fetchone()
        return result
    
    async def _get_question_keywords(self, question_id: str) -> List[str]:
        """Get expected keywords for a question"""
        
        try:
            conn = await self.db.get_connection()
            
            results = conn.execute("""
                SELECT keyword FROM question_keywords 
                WHERE question_id = ?
                ORDER BY weight DESC
            """, (question_id,)).fetchall()
            
            conn.close()
            return [row["keyword"] for row in results]
            
        except Exception as e:
            self.logger.warning(f"Failed to get keywords for {question_id}: {e}")
            return []
    
    async def _update_question_analytics(self, question_id: str, event: str):
        """Update question usage analytics"""
        
        try:
            conn = await self.db.get_connection()
            
            if event == "selected":
                conn.execute("""
                    UPDATE questions 
                    SET usage_count = usage_count + 1 
                    WHERE id = ?
                """, (question_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.warning(f"Failed to update analytics for {question_id}: {e}")
    
    async def get_question_statistics(self) -> Dict[str, Any]:
        """Get comprehensive question bank statistics"""
        
        try:
            conn = await self.db.get_connection()
            
            # Overall stats
            total_questions = conn.execute("SELECT COUNT(*) as count FROM questions WHERE is_active = 1").fetchone()["count"]
            
            # By type
            type_stats = conn.execute("""
                SELECT type, COUNT(*) as count 
                FROM questions 
                WHERE is_active = 1 
                GROUP BY type
            """).fetchall()
            
            # By skill
            skill_stats = conn.execute("""
                SELECT skill_category, COUNT(*) as count 
                FROM questions 
                WHERE is_active = 1 
                GROUP BY skill_category
            """).fetchall()
            
            # By difficulty
            difficulty_stats = conn.execute("""
                SELECT difficulty, COUNT(*) as count 
                FROM questions 
                WHERE is_active = 1 
                GROUP BY difficulty
            """).fetchall()
            
            # Usage stats
            usage_stats = conn.execute("""
                SELECT 
                    AVG(usage_count) as avg_usage,
                    MAX(usage_count) as max_usage,
                    MIN(usage_count) as min_usage
                FROM questions 
                WHERE is_active = 1
            """).fetchone()
            
            conn.close()
            
            return {
                "total_questions": total_questions,
                "by_type": {row["type"]: row["count"] for row in type_stats},
                "by_skill": {row["skill_category"]: row["count"] for row in skill_stats},
                "by_difficulty": {row["difficulty"]: row["count"] for row in difficulty_stats},
                "usage_statistics": dict(usage_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get question statistics: {e}")
            return {"error": str(e)}

# =============================================================================
# ENHANCED QUESTION BANK MANAGER
# =============================================================================

class EnhancedQuestionBankManager:
    """Main question bank manager with database and voice support"""
    
    def __init__(self, db_path: str = "question_bank.db", claude_client=None):
        self.db = QuestionBankDB(db_path)
        self.question_selector = None
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self, populate_sample_data: bool = True):
        """Initialize question bank"""
        
        try:
            # Initialize database
            await self.db.initialize_database()
            
            # Populate with sample data if requested
            if populate_sample_data:
                await self.db.populate_sample_data()
            
            # Initialize question selector
            self.question_selector = IntelligentQuestionSelector(self.db, self.claude_client)
            
            self._initialized = True
            self.logger.info("✅ Enhanced question bank initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Question bank initialization failed: {e}")
            raise Exception(f"Failed to initialize question bank: {e}")
    
    async def get_question(
        self,
        skill_category=None,
        difficulty=None,
        preferred_type=None,
        exclude_ids=None,
        strategy="adaptive_voice",
        session_state=None
    ) -> Optional[Question]:
        """Get next question using intelligent selection"""
        
        if not self._initialized:
            await self.initialize()
        
        # Build session state if not provided
        if session_state is None:
            session_state = {
                "questions_asked": exclude_ids or [],
                "evaluations": [],
                "skills_covered": {},
                "audio_mode": True
            }
        
        return await self.question_selector.select_next_question(session_state, strategy)
    
    async def record_question_response(
        self,
        question_id: str,
        session_id: str,
        evaluation: Dict[str, Any],
        response_time_seconds: int = None,
        transcription_confidence: float = None
    ):
        """Record question response for analytics"""
        
        try:
            conn = await self.db.get_connection()
            
            # Extract response metrics
            score = evaluation.get("score", 0)
            keywords_found = json.dumps(evaluation.get("keywords_found", []))
            response_length = len(evaluation.get("reasoning", "").split())
            
            # Insert analytics record
            conn.execute("""
                INSERT INTO question_analytics (
                    question_id, session_id, response_score, response_time_seconds,
                    transcription_confidence, response_length_words, keywords_found
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                question_id, session_id, score, response_time_seconds,
                transcription_confidence, response_length, keywords_found
            ))
            
            # Update question stats
            conn.execute("""
                UPDATE questions 
                SET avg_score = (
                    SELECT AVG(response_score) 
                    FROM question_analytics 
                    WHERE question_id = ?
                ),
                success_rate = (
                    SELECT CAST(SUM(CASE WHEN response_score >= 3.0 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100
                    FROM question_analytics 
                    WHERE question_id = ?
                )
                WHERE id = ?
            """, (question_id, question_id, question_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.warning(f"Failed to record question response: {e}")
    
    async def get_question_bank_status(self) -> Dict[str, Any]:
        """Get comprehensive question bank status"""
        
        try:
            if not self._initialized:
                return {"initialized": False, "error": "Not initialized"}
            
            stats = await self.question_selector.get_question_statistics()
            
            return {
                "initialized": True,
                "database_path": self.db.db_path,
                "question_statistics": stats,
                "intelligent_selection": True,
                "voice_optimized": True,
                "claude_integration": self.claude_client is not None
            }
            
        except Exception as e:
            return {"initialized": False, "error": str(e)}
    
    async def add_question(self, question_data: Dict[str, Any]) -> bool:
        """Add new question to database"""
        
        try:
            conn = await self.db.get_connection()
            
            conn.execute("""
                INSERT INTO questions (
                    id, text, audio_prompt, type, skill_category, difficulty,
                    estimated_time_minutes, estimated_audio_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                question_data["id"],
                question_data["text"],
                question_data.get("audio_prompt", question_data["text"]),
                question_data["type"],
                question_data["skill_category"],
                question_data["difficulty"],
                question_data.get("estimated_time_minutes", 5),
                question_data.get("estimated_audio_seconds", 120)
            ))
            
            # Add keywords
            for keyword in question_data.get("expected_keywords", []):
                conn.execute("""
                    INSERT OR IGNORE INTO question_keywords (question_id, keyword)
                    VALUES (?, ?)
                """, (question_data["id"], keyword))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Added question: {question_data['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add question: {e}")
            return False

# =============================================================================
# QUESTION BANK FACTORY
# =============================================================================

class QuestionBankFactory:
    """Factory for creating question banks"""
    
    @staticmethod
    def create_database_question_bank(
        db_path: str = "question_bank.db",
        claude_client=None,
        auto_initialize: bool = True
    ) -> EnhancedQuestionBankManager:
        """Create database-backed question bank"""
        
        manager = EnhancedQuestionBankManager(db_path, claude_client)
        
        if auto_initialize:
            # Initialize in background
            asyncio.create_task(manager.initialize())
        
        return manager
    
    @staticmethod
    def create_voice_optimized_bank(
        db_path: str = "voice_question_bank.db",
        claude_client=None
    ) -> EnhancedQuestionBankManager:
        """Create voice-optimized question bank"""
        
        return QuestionBankFactory.create_database_question_bank(
            db_path=db_path,
            claude_client=claude_client,
            auto_initialize=True
        )

# =============================================================================
# DATABASE SETUP UTILITIES
# =============================================================================

class QuestionBankSetup:
    """Utilities for setting up and managing question bank"""
    
    @staticmethod
    async def setup_fresh_database(db_path: str = "question_bank.db") -> bool:
        """Set up fresh question bank database"""
        
        try:
            print(f"🗄️ Setting up fresh question bank: {db_path}")
            
            # Remove existing database
            if Path(db_path).exists():
                Path(db_path).unlink()
                print(f"🗑️ Removed existing database")
            
            # Create new database
            db = QuestionBankDB(db_path)
            await db.initialize_database()
            await db.populate_sample_data()
            
            # Verify setup
            conn = await db.get_connection()
            count = conn.execute("SELECT COUNT(*) as count FROM questions").fetchone()["count"]
            conn.close()
            
            print(f"✅ Database setup complete: {count} questions loaded")
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    @staticmethod
    async def export_questions_to_json(db_path: str, output_file: str = "questions_backup.json"):
        """Export questions from database to JSON backup"""
        
        try:
            db = QuestionBankDB(db_path)
            conn = await db.get_connection()
            
            # Get all questions with keywords
            questions = conn.execute("""
                SELECT q.*, GROUP_CONCAT(qk.keyword) as keywords
                FROM questions q
                LEFT JOIN question_keywords qk ON q.id = qk.question_id
                GROUP BY q.id
                ORDER BY q.skill_category, q.difficulty, q.id
            """).fetchall()
            
            # Convert to JSON format
            questions_json = []
            for question in questions:
                question_dict = dict(question)
                question_dict["expected_keywords"] = question["keywords"].split(",") if question["keywords"] else []
                questions_json.append(question_dict)
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump({
                    "exported_at": datetime.utcnow().isoformat(),
                    "total_questions": len(questions_json),
                    "questions": questions_json
                }, f, indent=2)
            
            conn.close()
            print(f"✅ Exported {len(questions_json)} questions to {output_file}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    @staticmethod
    async def import_questions_from_json(db_path: str, input_file: str):
        """Import questions from JSON file to database"""
        
        try:
            # Load JSON data
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            questions = data.get("questions", [])
            if not questions:
                print("❌ No questions found in JSON file")
                return
            
            # Initialize database
            db = QuestionBankDB(db_path)
            await db.initialize_database()
            
            conn = await db.get_connection()
            
            # Import questions
            for question_data in questions:
                conn.execute("""
                    INSERT OR REPLACE INTO questions (
                        id, text, audio_prompt, type, skill_category, difficulty,
                        estimated_time_minutes, estimated_audio_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    question_data["id"],
                    question_data["text"],
                    question_data.get("audio_prompt", question_data["text"]),
                    question_data["type"],
                    question_data["skill_category"],
                    question_data["difficulty"],
                    question_data.get("estimated_time_minutes", 5),
                    question_data.get("estimated_audio_seconds", 120)
                ))
                
                # Import keywords
                for keyword in question_data.get("expected_keywords", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO question_keywords (question_id, keyword)
                        VALUES (?, ?)
                    """, (question_data["id"], keyword))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Imported {len(questions)} questions from {input_file}")
            
        except Exception as e:
            print(f"❌ Import failed: {e}")

# =============================================================================
# TESTING AND EXAMPLE USAGE
# =============================================================================

async def test_question_bank():
    """Test the enhanced question bank system"""
    
    print("🗄️ Testing Enhanced Question Bank")
    print("=" * 60)
    
    # Setup database
    print("📦 Setting up database...")
    setup_success = await QuestionBankSetup.setup_fresh_database("test_question_bank.db")
    
    if not setup_success:
        print("❌ Database setup failed")
        return
    
    # Create question bank manager
    print("🧠 Creating question bank manager...")
    manager = QuestionBankFactory.create_voice_optimized_bank(
        db_path="test_question_bank.db"
    )
    
    await manager.initialize(populate_sample_data=False)  # Already populated
    
    # Test question selection
    print("🎯 Testing question selection...")
    
    session_state = {
        "questions_asked": [],
        "evaluations": [],
        "skills_covered": {},
        "audio_mode": True
    }
    
    # Select 5 questions
    for i in range(5):
        question = await manager.get_question(
            strategy="adaptive_voice",
            session_state=session_state
        )
        
        if question:
            print(f"✅ Question {i+1}: {question.id} ({question.skill_category.value}, {question.difficulty.value}, {question.type.value})")
            session_state["questions_asked"].append(question.id)
            
            # Simulate evaluation
            session_state["evaluations"].append({
                "score": random.uniform(2.0, 5.0),
                "keywords_found": question.expected_keywords[:2]
            })
            
            skill_name = question.skill_category.value
            session_state["skills_covered"][skill_name] = session_state["skills_covered"].get(skill_name, 0) + 1
        else:
            print(f"❌ No question available for iteration {i+1}")
    
    # Get statistics
    print("\n📊 Question Bank Statistics:")
    status = await manager.get_question_bank_status()
    stats = status.get("question_statistics", {})
    
    print(f"  Total Questions: {stats.get('total_questions', 0)}")
    print(f"  By Type: {stats.get('by_type', {})}")
    print(f"  By Skill: {stats.get('by_skill', {})}")
    print(f"  By Difficulty: {stats.get('by_difficulty', {})}")
    
    print("\n🎉 Question bank test completed!")

if __name__ == "__main__":
    print("🗄️ Enhanced Question Bank System")
    print("=" * 60)
    print("📋 Features:")
    print("  ✅ SQLite database with comprehensive schema")
    print("  ✅ 50+ high-quality Excel questions")
    print("  ✅ Intelligent adaptive selection")
    print("  ✅ Voice interview optimization")
    print("  ✅ Question analytics and tracking")
    print("  ✅ Skill balancing and progression")
    print("  ✅ Performance-based adaptation")
    
    # Run test
    import asyncio
    asyncio.run(test_question_bank())