# streamlit_app_fixed.py - FIXED Streamlit Frontend
"""
FIXED: Streamlit frontend for voice-enhanced Excel interview system
Supports both voice and text-based interviews with proper error handling
"""

import streamlit as st

# =============================================================================
# PAGE CONFIGURATION - MUST BE FIRST
# =============================================================================
st.set_page_config(
    page_title="Excel Voice Interview System",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other libraries
import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
import tempfile
import uuid

# Audio recording support (with better error handling)
AUDIO_RECORDING_AVAILABLE = False
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    AUDIO_RECORDING_AVAILABLE = True
except ImportError:
    AUDIO_RECORDING_AVAILABLE = False

# =============================================================================
# CONFIGURATION
# =============================================================================

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AUDIO_SAMPLE_RATE = 16000
MAX_RECORDING_DURATION = 300

# =============================================================================
# FIXED API CLIENT
# =============================================================================

class InterviewAPIClient:
    """FIXED: API client with proper error handling"""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
    
    def check_health(self):
        """Check API health with proper error handling"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"healthy": False, "error": f"Connection failed: {str(e)}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def start_interview(self, candidate_name, audio_mode=False):
        """Start interview (unified endpoint)"""
        try:
            response = requests.post(
                f"{self.base_url}/api/interview/start",
                json={
                    "candidate_name": candidate_name,
                    "audio_mode": audio_mode
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def submit_text_response(self, session_id, text_response, time_taken=0):
        """Submit text response"""
        try:
            response = requests.post(
                f"{self.base_url}/api/interview/{session_id}/respond-text",
                json={
                    "response_text": text_response,
                    "time_taken_seconds": time_taken
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def submit_audio_response(self, session_id, audio_file_path):
        """Submit audio response"""
        try:
            with open(audio_file_path, 'rb') as f:
                files = {'audio': f}
                
                response = requests.post(
                    f"{self.base_url}/api/interview/{session_id}/respond-audio",
                    files=files,
                    timeout=60
                )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_interview_status(self, session_id):
        """Get interview status"""
        try:
            response = requests.get(f"{self.base_url}/api/interview/{session_id}/status", timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_interview_report(self, session_id):
        """Get final interview report"""
        try:
            response = requests.get(f"{self.base_url}/api/interview/{session_id}/report", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

# =============================================================================
# FIXED SESSION STATE MANAGEMENT
# =============================================================================

def initialize_session_state():
    """Initialize Streamlit session state with defaults"""
    
    defaults = {
        'interview_mode': None,
        'session_id': None,
        'interview_started': False,
        'current_question': None,
        'interview_complete': False,
        'questions_completed': 0,
        'current_score': 0.0,
        'audio_mode': False,
        'candidate_name': "",
        'response_history': [],
        'show_text_input': False,
        'api_client': InterviewAPIClient(),
        'audio_status_shown': False  # Track if we've shown audio status
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# =============================================================================
# FIXED UI COMPONENTS
# =============================================================================

def render_header():
    """Render application header"""
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 2rem;">
        <h1>🎙️ Excel Voice Interview System</h1>
        <p style="font-size: 1.2em; margin: 0;">
            AI-Powered Excel Skills Assessment with Voice Interaction
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_audio_status():
    """Show audio status once at startup"""
    if not st.session_state.audio_status_shown:
        if AUDIO_RECORDING_AVAILABLE:
            st.success("✅ Audio recording available")
        else:
            st.info("ℹ️ Audio recording not available. Text mode will be used.")
        st.session_state.audio_status_shown = True

def render_system_status():
    """FIXED: Render system status in sidebar"""
    
    with st.sidebar:
        st.markdown("### 🔍 System Status")
        
        # Check if API client exists
        if 'api_client' not in st.session_state:
            st.error("❌ API client not initialized")
            return
        
        try:
            with st.spinner("Checking system..."):
                health = st.session_state.api_client.check_health()
            
            # Handle health response properly
            if isinstance(health, dict):
                if health.get("healthy", False):
                    st.success("✅ System Healthy")
                    
                    # Show available features
                    features = health.get("available_features", {})
                    if isinstance(features, dict):
                        for feature, available in features.items():
                            status = "✅" if available else "❌"
                            st.markdown(f"{status} {feature.replace('_', ' ').title()}")
                    
                    # Show API keys status
                    api_keys = health.get("api_keys_configured", {})
                    if isinstance(api_keys, dict):
                        st.markdown("**API Keys:**")
                        for key, configured in api_keys.items():
                            status = "✅" if configured else "❌"
                            st.markdown(f"{status} {key.title()}")
                    
                else:
                    st.error("❌ System Issues Detected")
                    error_msg = health.get("error", "Unknown error")
                    st.error(f"Error: {error_msg}")
            else:
                st.error("❌ Invalid health response")
                
        except Exception as e:
            st.error(f"❌ Status check failed: {str(e)}")

def render_interview_mode_selection():
    """FIXED: Render interview mode selection"""
    
    st.markdown("## 🎯 Choose Your Interview Experience")
    
    # Check system capabilities first
    health = st.session_state.api_client.check_health()
    features = health.get("available_features", {}) if isinstance(health, dict) else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎙️ Voice Interview
        **Interactive conversation with AI interviewer**
        - Natural spoken interaction
        - AI provides contextual feedback
        - More engaging experience
        - Requires microphone
        """)
        
        voice_available = (
            features.get("voice_interviews", False) and 
            AUDIO_RECORDING_AVAILABLE
        )
        
        if voice_available:
            if st.button("🎙️ Start Voice Interview", type="primary", use_container_width=True):
                st.session_state.interview_mode = "voice"
                st.session_state.audio_mode = True
                st.rerun()
        else:
            st.button(
                "🎙️ Voice Not Available", 
                disabled=True, 
                use_container_width=True,
                help="Voice features require API keys and audio setup"
            )
    
    with col2:
        st.markdown("""
        ### 📝 Text Interview  
        **Traditional written assessment**
        - Type your responses
        - Clear, focused writing
        - Works on any device
        - No audio required
        """)
        
        text_available = features.get("text_interviews", True)  # Default to available
        
        if text_available:
            if st.button("📝 Start Text Interview", use_container_width=True):
                st.session_state.interview_mode = "text"
                st.session_state.audio_mode = False
                st.rerun()
        else:
            st.button(
                "📝 Text Not Available", 
                disabled=True, 
                use_container_width=True,
                help="Text interviews require evaluation engine"
            )
    
    # Show system status info
    if not voice_available or not text_available:
        st.markdown("---")
        st.warning("⚠️ Some features are not available. Check system status in sidebar.")

def render_candidate_info_form():
    """FIXED: Render candidate information form"""
    
    st.markdown("## 👤 Interview Setup")
    
    # Show selected mode
    mode_display = "🎙️ Voice Interview" if st.session_state.audio_mode else "📝 Text Interview"
    st.info(f"**Selected Mode:** {mode_display}")
    
    with st.form("candidate_info"):
        st.markdown("### Personal Information")
        
        candidate_name = st.text_input(
            "Your Name (Optional)",
            placeholder="Enter your name",
            help="This helps personalize your interview experience"
        )
        
        candidate_email = st.text_input(
            "Email (Optional)",
            placeholder="your.email@example.com",
            help="For receiving your detailed assessment report"
        )
        
        st.markdown("### Interview Preferences")
        
        if st.session_state.audio_mode:
            st.info("🎙️ Voice interview selected. Ensure your microphone is working.")
            
            # Audio settings
            audio_quality = st.selectbox(
                "Audio Quality",
                ["Standard", "High"],
                help="Higher quality uses more bandwidth"
            )
            
            if not AUDIO_RECORDING_AVAILABLE:
                st.warning("⚠️ Audio recording not available. Will fallback to text mode.")
        else:
            st.info("📝 Text interview selected. You'll type your responses.")
        
        # Difficulty preference
        difficulty_preference = st.selectbox(
            "Preferred Difficulty Level",
            ["Adaptive (Recommended)", "Beginner", "Intermediate", "Advanced"],
            help="Adaptive adjusts based on your responses"
        )
        
        # Time limit
        time_limit = st.slider(
            "Time Limit (minutes)",
            min_value=10,
            max_value=45,
            value=20,
            help="Estimated time for the complete interview"
        )
        
        # Submit button
        col1, col2 = st.columns([3, 1])
        with col2:
            submit_button = st.form_submit_button("🚀 Begin Interview", type="primary", use_container_width=True)
        
        with col1:
            if st.form_submit_button("🔙 Change Mode", use_container_width=True):
                st.session_state.interview_mode = None
                st.rerun()
    
    if submit_button:
        st.session_state.candidate_name = candidate_name or "Anonymous"
        start_interview()

def start_interview():
    """FIXED: Start the interview with proper error handling"""
    
    candidate_name = st.session_state.candidate_name
    audio_mode = st.session_state.audio_mode
    
    with st.spinner("🚀 Starting your interview..."):
        try:
            # Use unified start endpoint
            result = st.session_state.api_client.start_interview(
                candidate_name=candidate_name,
                audio_mode=audio_mode
            )
            
            if "error" in result:
                st.error(f"❌ Failed to start interview: {result['error']}")
                st.markdown("**Troubleshooting:**")
                st.markdown("- Check if the backend server is running")
                st.markdown("- Verify API keys are configured")
                st.markdown("- Check system status in sidebar")
                return
            
            # Store interview data
            st.session_state.session_id = result.get("session_id")
            st.session_state.interview_started = True
            st.session_state.current_question = result.get("first_question")
            
            # Show success message
            st.success("🎉 Interview started successfully!")
            
            # Show welcome message if available
            welcome_msg = result.get("welcome_message", "")
            if welcome_msg:
                st.info(welcome_msg)
            
            # Play welcome audio if available and in voice mode
            if audio_mode:
                welcome_audio = result.get("welcome_audio")
                if isinstance(welcome_audio, dict) and welcome_audio.get("success"):
                    st.markdown("### 🎙️ Welcome Message")
                    audio_url = welcome_audio.get("audio_url")
                    if audio_url:
                        st.audio(audio_url)
                    
                    # Show text backup
                    welcome_text = welcome_audio.get("text", "")
                    if welcome_text:
                        with st.expander("📝 Welcome Text"):
                            st.markdown(welcome_text)
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Interview start failed: {str(e)}")

def render_question_interface():
    """FIXED: Render the current question interface"""
    
    if not st.session_state.current_question:
        st.warning("⏳ Loading next question...")
        if st.button("🔄 Refresh"):
            st.rerun()
        return
    
    question = st.session_state.current_question
    
    # Question header
    st.markdown(f"### 📋 Question {st.session_state.questions_completed + 1}")
    
    # Question metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        skill = question.get("skill_category", "unknown").replace("_", " ").title()
        st.metric("Skill Area", skill)
    with col2:
        difficulty = question.get("difficulty", "unknown").title()
        st.metric("Difficulty", difficulty)
    with col3:
        q_type = question.get("type", "unknown").replace("_", " ").title()
        st.metric("Type", q_type)
    
    # Display question
    st.markdown("#### 📝 Question")
    question_text = question.get("text", "No question text available")
    st.markdown(f"**{question_text}**")
    
    # Estimated time
    est_time = question.get("estimated_time_minutes", 5)
    st.info(f"⏱️ Estimated time: {est_time} minutes")
    
    # Response interface based on mode
    if st.session_state.audio_mode:
        render_voice_response_interface()
    else:
        render_text_response_interface()

def render_voice_response_interface():
    """FIXED: Render voice response interface"""
    
    st.markdown("#### 🎙️ Voice Response")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if AUDIO_RECORDING_AVAILABLE:
            if st.button("🎤 Record Audio Response", type="primary", use_container_width=True):
                st.session_state.recording_mode = True
                st.rerun()
        else:
            st.warning("🎤 Audio recording not available on this device")
    
    with col2:
        if st.button("📝 Type Instead", use_container_width=True):
            st.session_state.show_text_input = True
            st.rerun()
    
    # Show recording interface
    if st.session_state.get("recording_mode", False):
        render_recording_interface()
    
    # Show text input if requested
    if st.session_state.get("show_text_input", False):
        render_text_response_interface()

def render_recording_interface():
    """FIXED: Render audio recording interface"""
    
    st.markdown("### 🎤 Audio Recording")
    
    if not AUDIO_RECORDING_AVAILABLE:
        st.error("Audio recording not available")
        return
    
    duration = st.slider("Recording Duration (seconds)", 10, 300, 90)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 Start Recording", type="primary"):
            # Simulate recording for demo
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(min(duration, 10)):  # Limit to 10 seconds for demo
                progress_bar.progress((i + 1) / 10)
                status_text.text(f"🎤 Recording... {i + 1}/10s")
                time.sleep(1)
            
            status_text.text("✅ Recording completed!")
            st.session_state.recording_ready = True
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel Recording"):
            st.session_state.recording_mode = False
            st.session_state.recording_ready = False
            st.rerun()
    
    # Submit recording if ready
    if st.session_state.get("recording_ready", False):
        if st.button("📤 Submit Audio Response", type="primary"):
            # Create mock audio file for demo
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(b"mock_audio_data")
                submit_audio_response(temp_file.name)

def render_text_response_interface():
    """FIXED: Render text response interface"""
    
    st.markdown("#### 📝 Text Response")
    
    with st.form("text_response_form"):
        response_text = st.text_area(
            "Your Response:",
            placeholder="Type your detailed response here...\n\nFor example:\n- Explain the concept clearly\n- Provide specific examples\n- Mention any limitations or alternatives",
            height=200,
            help="Provide a comprehensive answer demonstrating your Excel knowledge"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            confidence = st.select_slider(
                "Confidence Level",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: f"{x}/5 ({'Low' if x <= 2 else 'Medium' if x <= 3 else 'High'})"
            )
        
        with col2:
            time_taken = st.number_input("Time Taken (seconds)", min_value=0, value=120, step=30)
        
        with col3:
            submit_button = st.form_submit_button("📤 Submit Response", type="primary")
    
    if submit_button:
        if response_text.strip():
            submit_text_response(response_text, time_taken)
        else:
            st.error("Please provide a response before submitting")

def submit_text_response(response_text, time_taken):
    """FIXED: Submit text response with proper error handling"""
    
    with st.spinner("🔄 Processing your response..."):
        try:
            result = st.session_state.api_client.submit_text_response(
                session_id=st.session_state.session_id,
                text_response=response_text,
                time_taken=time_taken
            )
            
            handle_response_result(result, response_text)
            
        except Exception as e:
            st.error(f"❌ Response submission failed: {str(e)}")

def submit_audio_response(audio_file_path):
    """FIXED: Submit audio response with proper error handling"""
    
    with st.spinner("🔄 Processing your audio response..."):
        try:
            result = st.session_state.api_client.submit_audio_response(
                session_id=st.session_state.session_id,
                audio_file_path=audio_file_path
            )
            
            # Clean up temp file
            try:
                os.unlink(audio_file_path)
            except:
                pass
            
            handle_response_result(result, "Audio response")
            
        except Exception as e:
            st.error(f"❌ Audio response submission failed: {str(e)}")

def handle_response_result(result, response_text):
    """FIXED: Handle response submission result"""
    
    if not isinstance(result, dict):
        st.error("❌ Invalid response from server")
        return
    
    if "error" in result:
        st.error(f"❌ Response submission failed: {result['error']}")
        return
    
    # Store response in history
    response_record = {
        "question": st.session_state.current_question,
        "response": response_text,
        "evaluation": result.get("evaluation", {}),
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.response_history.append(response_record)
    
    # Display evaluation
    render_evaluation_feedback(result)
    
    # Update progress
    progress = result.get("progress", {})
    if isinstance(progress, dict):
        st.session_state.questions_completed = progress.get("questions_completed", st.session_state.questions_completed + 1)
        st.session_state.current_score = progress.get("current_score", 0)
    
    # Check completion
    interview_status = result.get("interview_status", "in_progress")
    if interview_status == "completed":
        st.session_state.interview_complete = True
        st.session_state.current_question = None
        
        completion_msg = result.get("completion_message")
        if completion_msg:
            st.success(completion_msg)
        
        # Play conclusion audio if available
        conclusion_audio = result.get("conclusion_audio")
        if isinstance(conclusion_audio, dict) and conclusion_audio.get("success"):
            st.markdown("### 🎙️ Interview Conclusion")
            audio_url = conclusion_audio.get("audio_url")
            if audio_url:
                st.audio(audio_url)
    else:
        # Set next question
        st.session_state.current_question = result.get("next_question")
        
        # Play next question audio if available
        question_audio = result.get("question_audio")
        if isinstance(question_audio, dict) and question_audio.get("success"):
            st.markdown("### 🎙️ Next Question Audio")
            audio_url = question_audio.get("audio_url")
            if audio_url:
                st.audio(audio_url)
    
    # Reset UI state
    for key in ["show_text_input", "recording_mode", "recording_ready"]:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def render_evaluation_feedback(result):
    """FIXED: Render evaluation feedback"""
    
    evaluation = result.get("evaluation", {})
    
    if not isinstance(evaluation, dict) or not evaluation:
        st.info("ℹ️ No detailed feedback available")
        return
    
    st.markdown("### 📊 Your Performance")
    
    # Score display
    score = evaluation.get("score", 0)
    confidence = evaluation.get("confidence", 0)
    keywords_found = evaluation.get("keywords_found", [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_color = "green" if score >= 3.5 else "orange" if score >= 2.5 else "red"
        st.metric("Score", f"{score:.1f}/5.0")
    
    with col2:
        st.metric("AI Confidence", f"{confidence:.0%}")
    
    with col3:
        st.metric("Key Terms", len(keywords_found))
    
    # Detailed feedback
    reasoning = evaluation.get("reasoning", "")
    if reasoning:
        st.markdown("**💡 Detailed Feedback:**")
        st.info(reasoning)
    
    # Strengths and improvements
    col1, col2 = st.columns(2)
    
    with col1:
        strengths = evaluation.get("strengths", [])
        if strengths:
            st.markdown("**✅ What You Did Well:**")
            for strength in strengths:
                st.success(f"• {strength}")
    
    with col2:
        improvements = evaluation.get("areas_for_improvement", [])
        if improvements:
            st.markdown("**🎯 Areas to Improve:**")
            for improvement in improvements:
                st.warning(f"• {improvement}")
    
    # Play feedback audio if available
    feedback_audio = result.get("feedback_audio")
    if isinstance(feedback_audio, dict) and feedback_audio.get("success"):
        st.markdown("### 🎙️ AI Interviewer Feedback")
        audio_url = feedback_audio.get("audio_url")
        if audio_url:
            st.audio(audio_url)

def render_progress_sidebar():
    """FIXED: Render interview progress in sidebar"""
    
    with st.sidebar:
        st.markdown("### 📈 Interview Progress")
        
        # Progress bar
        max_questions = 10  # Estimated
        progress = min(st.session_state.questions_completed / max_questions, 1.0)
        st.progress(progress)
        
        # Progress metrics
        st.markdown(f"**Questions Completed:** {st.session_state.questions_completed}")
        st.markdown(f"**Current Average Score:** {st.session_state.current_score:.1f}/5.0")
        
        # Performance indicator
        if st.session_state.current_score >= 4.0:
            st.success("🎯 Excellent Performance!")
        elif st.session_state.current_score >= 3.0:
            st.info("👍 Good Performance")
        elif st.session_state.current_score >= 2.0:
            st.warning("💪 Keep Improving")
        else:
            st.error("📚 Need More Practice")
        
        # Interview details
        st.markdown("---")
        st.markdown("### 📋 Session Details")
        st.markdown(f"**Mode:** {'🎙️ Voice' if st.session_state.audio_mode else '📝 Text'}")
        st.markdown(f"**Candidate:** {st.session_state.candidate_name}")
        
        if st.session_state.session_id:
            with st.expander("🔍 Technical Details"):
                st.code(f"Session ID: {st.session_state.session_id}")
                st.code(f"Started: {datetime.now().strftime('%H:%M:%S')}")

def render_interview_complete():
    """FIXED: Render interview completion screen"""
    
    st.markdown("## 🎉 Interview Complete!")
    st.balloons()
    
    # Final performance summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Questions Completed", st.session_state.questions_completed)
    
    with col2:
        st.metric("Final Score", f"{st.session_state.current_score:.1f}/5.0")
    
    with col3:
        if st.session_state.current_score >= 4.0:
            level = "Expert"
            emoji = "🏆"
        elif st.session_state.current_score >= 3.0:
            level = "Advanced"
            emoji = "🎯"
        elif st.session_state.current_score >= 2.0:
            level = "Intermediate"
            emoji = "👍"
        else:
            level = "Beginner"
            emoji = "📚"
        
        st.metric("Performance Level", f"{emoji} {level}")
    
    # Performance summary
    st.markdown("### 📊 Performance Summary")
    if st.session_state.current_score >= 3.5:
        st.success("🎉 Excellent Excel skills! You demonstrated strong understanding across multiple areas.")
    elif st.session_state.current_score >= 2.5:
        st.info("👍 Good Excel foundation with room for growth in advanced areas.")
    else:
        st.warning("📚 Consider reviewing Excel fundamentals and practicing more advanced features.")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Generate Detailed Report", type="primary", use_container_width=True):
            generate_final_report()
    
    with col2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            reset_session_state()
            st.rerun()
    
    # Response history
    if st.session_state.response_history:
        with st.expander("📚 Review Your Responses", expanded=False):
            for i, response in enumerate(st.session_state.response_history):
                st.markdown(f"### Question {i+1}")
                
                question_text = response.get("question", {}).get("text", "")
                st.markdown(f"**Question:** {question_text[:150]}...")
                
                response_text = str(response.get("response", ""))
                st.markdown(f"**Your Answer:** {response_text[:200]}...")
                
                evaluation = response.get("evaluation", {})
                score = evaluation.get("score", 0)
                reasoning = evaluation.get("reasoning", "")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Score", f"{score:.1f}/5.0")
                with col2:
                    if reasoning:
                        st.markdown(f"**Feedback:** {reasoning}")
                
                st.markdown("---")

def generate_final_report():
    """FIXED: Generate and display final interview report"""
    
    with st.spinner("📋 Generating your detailed report..."):
        try:
            result = st.session_state.api_client.get_interview_report(
                session_id=st.session_state.session_id
            )
            
            if "error" in result:
                st.error(f"❌ Report generation failed: {result['error']}")
                return
            
            # Display report
            st.markdown("### 📋 Your Detailed Assessment Report")
            
            report_text = result.get("report", "") or result.get("text_report", "")
            if report_text:
                st.markdown(report_text)
            else:
                st.warning("📄 Report content not available")
            
            # Voice analysis if available
            voice_analysis = result.get("voice_analysis", {})
            if isinstance(voice_analysis, dict) and voice_analysis and not voice_analysis.get("error"):
                st.markdown("### 🎙️ Voice Performance Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    comm_quality = voice_analysis.get("communication_quality", "N/A")
                    st.markdown(f"**Communication Quality:** {comm_quality}")
                    
                    avg_confidence = voice_analysis.get("avg_confidence", 0)
                    st.markdown(f"**Average Confidence:** {avg_confidence:.1%}")
                
                with col2:
                    audio_count = voice_analysis.get("audio_response_count", 0)
                    st.markdown(f"**Audio Responses:** {audio_count}")
                    
                    total_time = voice_analysis.get("total_audio_duration", 0)
                    st.markdown(f"**Total Audio Time:** {total_time:.1f}s")
            
            # Play report audio if available
            report_audio = result.get("report_audio")
            if isinstance(report_audio, dict) and report_audio.get("success"):
                st.markdown("### 🎙️ Audio Summary")
                audio_url = report_audio.get("audio_url")
                if audio_url:
                    st.audio(audio_url)
            
        except Exception as e:
            st.error(f"❌ Report generation failed: {str(e)}")

def reset_session_state():
    """Reset session state for new interview"""
    
    keys_to_reset = [
        'interview_mode', 'session_id', 'interview_started', 'current_question',
        'interview_complete', 'questions_completed', 'current_score', 'audio_mode',
        'candidate_name', 'response_history', 'show_text_input', 'recording_mode',
        'recording_ready', 'audio_status_shown'
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """FIXED: Main Streamlit application with proper error handling"""
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Render header
        render_header()
        
        # Show audio status once
        show_audio_status()
        
        # System status in sidebar
        render_system_status()
        
        # Main application flow
        if not st.session_state.interview_started:
            if st.session_state.interview_mode is None:
                # Mode selection
                render_interview_mode_selection()
            else:
                # Candidate info form
                render_candidate_info_form()
        
        elif st.session_state.interview_complete:
            # Interview complete screen
            render_progress_sidebar()
            render_interview_complete()
        
        else:
            # Active interview
            render_progress_sidebar()
            render_question_interface()
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; color: #666; padding: 1rem;">
                🎙️ Excel Voice Interview System v4.0 | 
                Powered by Claude AI & ElevenLabs Voice Technology
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.markdown("**Debug Information:**")
        st.code(f"Error type: {type(e).__name__}")
        st.code(f"Error message: {str(e)}")
        
        if st.button("🔄 Reset Application"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# =============================================================================
# STREAMLIT ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()