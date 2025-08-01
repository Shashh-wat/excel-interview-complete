# system_config.py - System Feature Configuration
"""
Simple configuration system to control which features are enabled.
Allows you to start simple and add complexity as needed.
"""

import os
from typing import Dict, Any

class SystemConfig:
    """System configuration for enabling/disabling features"""
    
    def __init__(self):
        # =============================================================================
        # CORE FEATURES (Always Enabled)
        # =============================================================================
        self.evaluation_engine_enabled = True
        self.interview_orchestrator_enabled = True
        
        # =============================================================================
        # OPTIONAL ENHANCEMENTS (Can be disabled)
        # =============================================================================
        
        # Session Management
        self.session_persistence_enabled = self._get_bool_env('ENABLE_SESSION_PERSISTENCE', False)
        self.session_analytics_enabled = self._get_bool_env('ENABLE_SESSION_ANALYTICS', False)
        
        # Question Bank Features  
        self.question_analytics_enabled = self._get_bool_env('ENABLE_QUESTION_ANALYTICS', False)
        self.question_caching_enabled = self._get_bool_env('ENABLE_QUESTION_CACHING', False)
        self.question_generation_enabled = self._get_bool_env('ENABLE_QUESTION_GENERATION', False)
        
        # Database Features
        self.redis_enabled = self._get_bool_env('ENABLE_REDIS', False)
        self.sqlite_persistence_enabled = self._get_bool_env('ENABLE_SQLITE_PERSISTENCE', False)
        
        # Advanced Features
        self.advanced_analytics_enabled = self._get_bool_env('ENABLE_ADVANCED_ANALYTICS', False)
        self.multi_model_evaluation_enabled = self._get_bool_env('ENABLE_MULTI_MODEL_EVALUATION', False)
        
        # =============================================================================
        # PERFORMANCE SETTINGS
        # =============================================================================
        self.cache_ttl_minutes = int(os.getenv('CACHE_TTL_MINUTES', 5))
        self.max_concurrent_evaluations = int(os.getenv('MAX_CONCURRENT_EVALUATIONS', 10))
        self.session_cleanup_hours = int(os.getenv('SESSION_CLEANUP_HOURS', 24))
        
        # =============================================================================
        # FEATURE PRESETS
        # =============================================================================
        preset = os.getenv('SYSTEM_PRESET', 'minimal').lower()
        self._apply_preset(preset)
    
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')
    
    def _apply_preset(self, preset: str):
        """Apply feature preset"""
        
        if preset == 'minimal':
            # Just core features - what you have working now
            self.session_persistence_enabled = False
            self.question_analytics_enabled = False
            self.redis_enabled = False
            self.advanced_analytics_enabled = False
            
        elif preset == 'basic':
            # Add simple persistence and analytics
            self.session_persistence_enabled = True
            self.question_analytics_enabled = True
            self.sqlite_persistence_enabled = True
            self.redis_enabled = False
            self.advanced_analytics_enabled = False
            
        elif preset == 'enhanced':
            # Add caching and more features
            self.session_persistence_enabled = True
            self.question_analytics_enabled = True
            self.question_caching_enabled = True
            self.sqlite_persistence_enabled = True
            self.redis_enabled = True
            self.advanced_analytics_enabled = True
            
        elif preset == 'full':
            # Enable everything
            self.session_persistence_enabled = True
            self.session_analytics_enabled = True
            self.question_analytics_enabled = True
            self.question_caching_enabled = True
            self.question_generation_enabled = True
            self.sqlite_persistence_enabled = True
            self.redis_enabled = True
            self.advanced_analytics_enabled = True
            self.multi_model_evaluation_enabled = True
    
    def get_enabled_features(self) -> Dict[str, bool]:
        """Get list of enabled features"""
        return {
            "core": {
                "evaluation_engine": self.evaluation_engine_enabled,
                "interview_orchestrator": self.interview_orchestrator_enabled
            },
            "session_management": {
                "persistence": self.session_persistence_enabled,
                "analytics": self.session_analytics_enabled
            },
            "question_bank": {
                "analytics": self.question_analytics_enabled,
                "caching": self.question_caching_enabled,
                "generation": self.question_generation_enabled
            },
            "storage": {
                "redis": self.redis_enabled,
                "sqlite_persistence": self.sqlite_persistence_enabled
            },
            "advanced": {
                "analytics": self.advanced_analytics_enabled,
                "multi_model": self.multi_model_evaluation_enabled
            }
        }
    
    def should_use_enhancement(self, feature_name: str) -> bool:
        """Check if a specific enhancement should be used"""
        return getattr(self, f"{feature_name}_enabled", False)
    
    def get_recommendations(self) -> Dict[str, Any]:
        """Get recommendations based on current configuration"""
        
        enabled_count = sum([
            self.session_persistence_enabled,
            self.question_analytics_enabled,
            self.redis_enabled,
            self.advanced_analytics_enabled
        ])
        
        if enabled_count == 0:
            return {
                "level": "minimal",
                "description": "Core features only - good for getting started",
                "next_step": "Consider enabling session persistence for better reliability",
                "complexity": "low"
            }
        elif enabled_count <= 2:
            return {
                "level": "basic", 
                "description": "Basic enhancements enabled - good balance",
                "next_step": "Consider enabling Redis for better performance",
                "complexity": "medium"
            }
        else:
            return {
                "level": "advanced",
                "description": "Multiple enhancements enabled - feature-rich setup",
                "next_step": "Monitor performance and optimize as needed",
                "complexity": "high"
            }

# =============================================================================
# GLOBAL CONFIG INSTANCE
# =============================================================================

# Create global config instance
config = SystemConfig()

# =============================================================================
# PRESET EXAMPLES FOR .env
# =============================================================================

PRESET_EXAMPLES = {
    "minimal": """
# Minimal preset - just what's working now
SYSTEM_PRESET=minimal
# All enhancements disabled by default
""",
    
    "basic": """
# Basic preset - add simple persistence
SYSTEM_PRESET=basic
ENABLE_SESSION_PERSISTENCE=true
ENABLE_QUESTION_ANALYTICS=true
ENABLE_SQLITE_PERSISTENCE=true
""",
    
    "enhanced": """
# Enhanced preset - add caching and Redis
SYSTEM_PRESET=enhanced
ENABLE_SESSION_PERSISTENCE=true
ENABLE_QUESTION_ANALYTICS=true
ENABLE_QUESTION_CACHING=true
ENABLE_SQLITE_PERSISTENCE=true
ENABLE_REDIS=true
ENABLE_ADVANCED_ANALYTICS=true
""",
    
    "full": """
# Full preset - enable everything
SYSTEM_PRESET=full
ENABLE_SESSION_PERSISTENCE=true
ENABLE_SESSION_ANALYTICS=true
ENABLE_QUESTION_ANALYTICS=true
ENABLE_QUESTION_CACHING=true
ENABLE_QUESTION_GENERATION=true
ENABLE_SQLITE_PERSISTENCE=true
ENABLE_REDIS=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_MULTI_MODEL_EVALUATION=true
"""
}

def print_current_config():
    """Print current system configuration"""
    
    print("🔧 Current System Configuration")
    print("=" * 50)
    
    features = config.get_enabled_features()
    
    for category, category_features in features.items():
        print(f"\n📂 {category.replace('_', ' ').title()}:")
        for feature, enabled in category_features.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"   {feature.replace('_', ' ').title()}: {status}")
    
    recommendations = config.get_recommendations()
    print(f"\n💡 Current Level: {recommendations['level'].title()}")
    print(f"📝 Description: {recommendations['description']}")
    print(f"🎯 Next Step: {recommendations['next_step']}")
    print(f"⚖️ Complexity: {recommendations['complexity'].title()}")

def print_preset_examples():
    """Print preset examples for .env file"""
    
    print("\n🎛️ Preset Examples for .env file")
    print("=" * 50)
    
    for preset_name, preset_config in PRESET_EXAMPLES.items():
        print(f"\n### {preset_name.upper()} PRESET ###")
        print(preset_config.strip())

if __name__ == "__main__":
    print_current_config()
    print_preset_examples()