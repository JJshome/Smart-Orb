"""
Smart Orb: Stimulation Controller Module

This module implements the core adaptive stimulation control logic for 
exercise enhancement functionality in the Smart Orb device. It processes
physiological signals and adjusts TENS and multi-sensory stimulation
parameters in real-time based on exercise phase and user state.

Copyright (c) 2024 Ucaretron Inc.
"""

import numpy as np
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExercisePhase(Enum):
    """Exercise phases used to adjust stimulation parameters"""
    WARMUP = 0
    MAIN = 1
    PEAK = 2
    COOLDOWN = 3
    RECOVERY = 4

class StimulationType(Enum):
    """Types of stimulation provided by Smart Orb"""
    TENS = 0      # Transcutaneous Electrical Nerve Stimulation
    VISUAL = 1    # LED-based visual feedback
    AUDIO = 2     # Sound-based feedback 
    HAPTIC = 3    # Vibration-based tactile feedback
    THERMAL = 4   # Temperature-based feedback

class StimulationController:
    """
    Controls all aspects of stimulation delivery for the Smart Orb device
    during exercise enhancement.
    """
    
    def __init__(self, user_profile=None):
        """
        Initialize the stimulation controller with user profile if available
        
        Args:
            user_profile: Dictionary containing user preferences and physiological baselines
        """
        self.user_profile = user_profile if user_profile else self._default_profile()
        self.current_phase = ExercisePhase.WARMUP
        self.fatigue_level = 0.0  # 0.0 to 1.0 scale
        self.tens_params = {
            "frequency": 35.0,    # Hz
            "pulse_width": 200.0, # μs
            "intensity": 0.2,     # 0.0-1.0 scale
            "pattern": "continuous"
        }
        self.visual_params = {
            "color": (0, 200, 255),  # RGB
            "brightness": 0.5,        # 0.0-1.0 scale
            "pattern": "slow_pulse"
        }
        self.audio_params = {
            "volume": 0.4,            # 0.0-1.0 scale
            "frequency": 10.0,        # Hz (for binaural beats)
            "pattern": "nature"
        }
        self.haptic_params = {
            "intensity": 0.3,         # 0.0-1.0 scale
            "frequency": 50.0,        # Hz
            "pattern": "rhythmic"
        }
        self.thermal_params = {
            "temperature": 32.0,      # Celsius
            "pattern": "constant"
        }
        
        # Stimulation effectiveness tracking
        self.effectiveness_history = []
        logger.info("StimulationController initialized with default parameters")
    
    def _default_profile(self):
        """Create default user profile with safe parameters"""
        return {
            "max_heart_rate": 180,
            "resting_heart_rate": 65,
            "max_tens_intensity": 0.6,
            "preferred_audio": "nature",
            "preferred_color": "blue",
            "skin_sensitivity": "normal",
            "fatigue_threshold": 0.7
        }
    
    def update_physiological_state(self, heart_rate, emg_activity, gsr, acceleration, impedance_data):
        """
        Update internal state based on latest physiological measurements
        
        Args:
            heart_rate: Current heart rate in BPM
            emg_activity: Muscle activity level (0.0-1.0)
            gsr: Galvanic skin response (measure of stress/arousal)
            acceleration: Movement acceleration magnitude in m/s^2
            impedance_data: Raw electrochemical impedance measurements
        
        Returns:
            dict: Updated state information
        """
        # Calculate exercise intensity based on heart rate reserve
        max_hr = self.user_profile["max_heart_rate"]
        rest_hr = self.user_profile["resting_heart_rate"]
        heart_rate_reserve = (heart_rate - rest_hr) / (max_hr - rest_hr)
        intensity = max(0.0, min(1.0, heart_rate_reserve))
        
        # Determine exercise phase
        if intensity < 0.3:
            if self.current_phase in [ExercisePhase.MAIN, ExercisePhase.PEAK]:
                new_phase = ExercisePhase.COOLDOWN
            elif self.current_phase == ExercisePhase.COOLDOWN:
                new_phase = ExercisePhase.RECOVERY
            else:
                new_phase = ExercisePhase.WARMUP
        elif intensity < 0.7:
            new_phase = ExercisePhase.MAIN
        else:
            new_phase = ExercisePhase.PEAK
            
        # Phase transition logging
        if new_phase != self.current_phase:
            logger.info(f"Exercise phase transition: {self.current_phase.name} -> {new_phase.name}")
            self.current_phase = new_phase
            
        # Estimate fatigue level from EMG and heart rate data
        hr_contribution = 0.4 * heart_rate_reserve
        emg_contribution = 0.6 * self._analyze_emg_fatigue(emg_activity)
        new_fatigue = hr_contribution + emg_contribution
        
        # Apply temporal smoothing to fatigue estimate
        self.fatigue_level = 0.8 * self.fatigue_level + 0.2 * new_fatigue
        
        # Process impedance data to estimate hydration and muscle state
        hydration_level = self._estimate_hydration(impedance_data)
        
        return {
            "phase": self.current_phase,
            "intensity": intensity,
            "fatigue": self.fatigue_level,
            "hydration": hydration_level
        }
    
    def _analyze_emg_fatigue(self, emg_activity):
        """
        Analyze EMG signal characteristics to estimate muscle fatigue
        
        Args:
            emg_activity: Normalized EMG activity level
            
        Returns:
            float: Estimated fatigue level from 0.0 to 1.0
        """
        # In a real implementation, this would analyze frequency components
        # and amplitude changes in the EMG signal to detect fatigue markers
        # This is a simplified placeholder
        return emg_activity * 0.8
    
    def _estimate_hydration(self, impedance_data):
        """
        Estimate hydration level from electrochemical impedance analysis
        
        Args:
            impedance_data: Raw impedance measurements
            
        Returns:
            float: Estimated hydration level from 0.0 to 1.0
        """
        # In a real implementation, this would apply complex bioimpedance
        # analysis techniques to the multi-frequency impedance data
        # This is a simplified placeholder
        if isinstance(impedance_data, (int, float)):
            # Normalize a single value between typical ranges
            return max(0.0, min(1.0, (impedance_data - 400) / 200))
        else:
            # With actual multi-frequency data, we'd do proper analysis
            return 0.7  # Default reasonable value
    
    def adjust_stimulation(self):
        """
        Adjust all stimulation parameters based on current physiological state and exercise phase
        
        Returns:
            dict: Complete set of updated stimulation parameters
        """
        # Adjust TENS parameters based on exercise phase and fatigue
        self._adjust_tens_parameters()
        
        # Adjust multi-sensory feedback parameters
        self._adjust_visual_parameters()
        self._adjust_audio_parameters()
        self._adjust_haptic_parameters()
        self._adjust_thermal_parameters()
        
        # Return complete parameter set
        return {
            "tens": self.tens_params,
            "visual": self.visual_params,
            "audio": self.audio_params,
            "haptic": self.haptic_params,
            "thermal": self.thermal_params
        }
    
    def _adjust_tens_parameters(self):
        """Adjust TENS stimulation based on exercise phase and fatigue"""
        # Base frequency selection on exercise phase
        if self.current_phase == ExercisePhase.WARMUP:
            # Low frequency for muscle preparation
            self.tens_params["frequency"] = 10.0 + 15.0 * (1.0 - self.fatigue_level)
            self.tens_params["pulse_width"] = 150.0
            self.tens_params["pattern"] = "rhythmic"
            
        elif self.current_phase == ExercisePhase.MAIN:
            # Higher frequency for power output
            self.tens_params["frequency"] = 35.0 - 10.0 * self.fatigue_level
            self.tens_params["pulse_width"] = 200.0 + 50.0 * self.fatigue_level
            self.tens_params["pattern"] = "continuous"
            
        elif self.current_phase == ExercisePhase.PEAK:
            # Maximum frequency for peak performance
            self.tens_params["frequency"] = 50.0 - 15.0 * self.fatigue_level
            self.tens_params["pulse_width"] = 250.0
            self.tens_params["pattern"] = "burst"
            
        elif self.current_phase == ExercisePhase.COOLDOWN:
            # Medium-low frequency for controlled cooldown
            self.tens_params["frequency"] = 20.0
            self.tens_params["pulse_width"] = 200.0
            self.tens_params["pattern"] = "wave"
            
        elif self.current_phase == ExercisePhase.RECOVERY:
            # Low frequency for recovery enhancement
            self.tens_params["frequency"] = 5.0
            self.tens_params["pulse_width"] = 300.0
            self.tens_params["pattern"] = "long_pulse"
        
        # Adjust intensity based on fatigue level and user's max tolerance
        max_intensity = self.user_profile["max_tens_intensity"]
        phase_intensity = {
            ExercisePhase.WARMUP: 0.3,
            ExercisePhase.MAIN: 0.6,
            ExercisePhase.PEAK: 0.8,
            ExercisePhase.COOLDOWN: 0.4,
            ExercisePhase.RECOVERY: 0.3
        }
        
        # Reduce intensity when fatigue is high
        fatigue_factor = 1.0 - (0.3 * self.fatigue_level)
        
        # Calculate final intensity with safety cap
        base_intensity = phase_intensity[self.current_phase]
        self.tens_params["intensity"] = min(max_intensity, base_intensity * fatigue_factor)
    
    def _adjust_visual_parameters(self):
        """Adjust visual feedback based on exercise phase"""
        # Color selection based on exercise phase
        phase_colors = {
            ExercisePhase.WARMUP: (0, 200, 255),    # Blue
            ExercisePhase.MAIN: (0, 255, 0),        # Green
            ExercisePhase.PEAK: (255, 0, 0),        # Red
            ExercisePhase.COOLDOWN: (180, 180, 255), # Light blue
            ExercisePhase.RECOVERY: (150, 255, 220)  # Mint green
        }
        
        # Brightness and pattern based on intensity
        phase_brightness = {
            ExercisePhase.WARMUP: 0.5,
            ExercisePhase.MAIN: 0.7,
            ExercisePhase.PEAK: 0.9,
            ExercisePhase.COOLDOWN: 0.6,
            ExercisePhase.RECOVERY: 0.4
        }
        
        phase_pattern = {
            ExercisePhase.WARMUP: "slow_pulse",
            ExercisePhase.MAIN: "steady",
            ExercisePhase.PEAK: "fast_pulse",
            ExercisePhase.COOLDOWN: "wave",
            ExercisePhase.RECOVERY: "gentle_fade"
        }
        
        self.visual_params["color"] = phase_colors[self.current_phase]
        self.visual_params["brightness"] = phase_brightness[self.current_phase]
        self.visual_params["pattern"] = phase_pattern[self.current_phase]
    
    def _adjust_audio_parameters(self):
        """Adjust audio feedback based on exercise phase"""
        # Binaural beat frequency based on desired brain state for each phase
        phase_frequency = {
            ExercisePhase.WARMUP: 10.0,     # Alpha waves for focus
            ExercisePhase.MAIN: 16.0,       # Beta waves for alertness
            ExercisePhase.PEAK: 20.0,       # High beta for intensity
            ExercisePhase.COOLDOWN: 8.0,    # Alpha/theta border for relaxation
            ExercisePhase.RECOVERY: 6.0     # Theta waves for recovery
        }
        
        phase_volume = {
            ExercisePhase.WARMUP: 0.5,
            ExercisePhase.MAIN: 0.6,
            ExercisePhase.PEAK: 0.7,
            ExercisePhase.COOLDOWN: 0.5,
            ExercisePhase.RECOVERY: 0.4
        }
        
        # Audio pattern selection
        preferred_audio = self.user_profile.get("preferred_audio", "nature")
        
        phase_pattern = {
            ExercisePhase.WARMUP: preferred_audio,
            ExercisePhase.MAIN: "rhythm",
            ExercisePhase.PEAK: "motivational",
            ExercisePhase.COOLDOWN: preferred_audio,
            ExercisePhase.RECOVERY: "ambient"
        }
        
        self.audio_params["frequency"] = phase_frequency[self.current_phase]
        self.audio_params["volume"] = phase_volume[self.current_phase]
        self.audio_params["pattern"] = phase_pattern[self.current_phase]
    
    def _adjust_haptic_parameters(self):
        """Adjust haptic (vibration) feedback based on exercise phase"""
        phase_intensity = {
            ExercisePhase.WARMUP: 0.4,
            ExercisePhase.MAIN: 0.6,
            ExercisePhase.PEAK: 0.8,
            ExercisePhase.COOLDOWN: 0.5,
            ExercisePhase.RECOVERY: 0.3
        }
        
        phase_frequency = {
            ExercisePhase.WARMUP: 40.0,
            ExercisePhase.MAIN: 60.0,
            ExercisePhase.PEAK: 80.0,
            ExercisePhase.COOLDOWN: 50.0,
            ExercisePhase.RECOVERY: 30.0
        }
        
        phase_pattern = {
            ExercisePhase.WARMUP: "rhythmic",
            ExercisePhase.MAIN: "continuous",
            ExercisePhase.PEAK: "pulsed",
            ExercisePhase.COOLDOWN: "wave",
            ExercisePhase.RECOVERY: "gentle"
        }
        
        self.haptic_params["intensity"] = phase_intensity[self.current_phase]
        self.haptic_params["frequency"] = phase_frequency[self.current_phase]
        self.haptic_params["pattern"] = phase_pattern[self.current_phase]
    
    def _adjust_thermal_parameters(self):
        """Adjust thermal feedback based on exercise phase"""
        # Temperature selection based on exercise phase and user preference
        sensitivity = self.user_profile.get("skin_sensitivity", "normal")
        sensitivity_factor = 1.0 if sensitivity == "normal" else 0.8
        
        phase_temperature = {
            ExercisePhase.WARMUP: 35.0,     # Warm
            ExercisePhase.MAIN: 32.0,       # Neutral
            ExercisePhase.PEAK: 30.0,       # Slight cooling
            ExercisePhase.COOLDOWN: 28.0,   # Cooling
            ExercisePhase.RECOVERY: 33.0    # Mild warming
        }
        
        # Adjust temperature based on fatigue (more cooling when fatigued)
        base_temp = phase_temperature[self.current_phase]
        fatigue_adjustment = self.fatigue_level * -2.0  # Up to 2 degrees cooler
        
        self.thermal_params["temperature"] = base_temp + fatigue_adjustment
        self.thermal_params["pattern"] = "constant"
    
    def evaluate_effectiveness(self, performance_metrics):
        """
        Evaluate the effectiveness of current stimulation parameters
        
        Args:
            performance_metrics: Dict containing metrics like power output, 
                                endurance, perceived exertion, etc.
        
        Returns:
            float: Effectiveness score (0.0 to 1.0)
        """
        # This would implement a machine learning model to assess effectiveness
        # For now, we'll use a simplified heuristic
        
        if not performance_metrics:
            return 0.5  # Default score
            
        # Extract key metrics
        power = performance_metrics.get('power_output', 0.0)
        endurance = performance_metrics.get('endurance', 0.0)
        exertion = performance_metrics.get('perceived_exertion', 5.0)
        
        # Simple weighted scoring
        effectiveness = (0.4 * power + 0.4 * endurance + 0.2 * (10.0 - exertion)) / 10.0
        
        # Bound the score
        effectiveness = max(0.0, min(1.0, effectiveness))
        
        # Add to history for learning
        self.effectiveness_history.append({
            'score': effectiveness,
            'phase': self.current_phase,
            'parameters': {
                'tens': self.tens_params.copy(),
                'visual': self.visual_params.copy(),
                'audio': self.audio_params.copy(),
                'haptic': self.haptic_params.copy(),
                'thermal': self.thermal_params.copy()
            }
        })
        
        return effectiveness
    
    def save_session_data(self, filepath):
        """
        Save stimulation session data for later analysis
        
        Args:
            filepath: Path to save the session data
        """
        import json
        import time
        
        session_data = {
            'timestamp': time.time(),
            'user_profile': self.user_profile,
            'effectiveness_history': self.effectiveness_history,
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session data saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save session data: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Create a controller with a custom user profile
    user_profile = {
        "max_heart_rate": 185,
        "resting_heart_rate": 62,
        "max_tens_intensity": 0.7,
        "preferred_audio": "forest",
        "preferred_color": "blue",
        "skin_sensitivity": "normal",
        "fatigue_threshold": 0.8
    }
    
    controller = StimulationController(user_profile)
    
    # Simulate an exercise session
    print("Simulating exercise session...")
    
    # Warmup phase
    print("\n== Warmup Phase ==")
    state = controller.update_physiological_state(
        heart_rate=100, 
        emg_activity=0.3,
        gsr=0.4,
        acceleration=0.5,
        impedance_data=500
    )
    params = controller.adjust_stimulation()
    print(f"Phase: {state['phase'].name}, Fatigue: {state['fatigue']:.2f}")
    print(f"TENS: {params['tens']['frequency']}Hz at {params['tens']['intensity']*100:.0f}% intensity")
    print(f"Visual: {params['visual']['pattern']} pattern at {params['visual']['brightness']*100:.0f}% brightness")
    
    # Main exercise phase
    print("\n== Main Exercise Phase ==")
    state = controller.update_physiological_state(
        heart_rate=140, 
        emg_activity=0.6,
        gsr=0.7,
        acceleration=1.2,
        impedance_data=480
    )
    params = controller.adjust_stimulation()
    print(f"Phase: {state['phase'].name}, Fatigue: {state['fatigue']:.2f}")
    print(f"TENS: {params['tens']['frequency']}Hz at {params['tens']['intensity']*100:.0f}% intensity")
    print(f"Visual: {params['visual']['pattern']} pattern at {params['visual']['brightness']*100:.0f}% brightness")
    
    # Peak phase
    print("\n== Peak Phase ==")
    state = controller.update_physiological_state(
        heart_rate=170, 
        emg_activity=0.8,
        gsr=0.9,
        acceleration=1.8,
        impedance_data=460
    )
    params = controller.adjust_stimulation()
    print(f"Phase: {state['phase'].name}, Fatigue: {state['fatigue']:.2f}")
    print(f"TENS: {params['tens']['frequency']}Hz at {params['tens']['intensity']*100:.0f}% intensity")
    print(f"Visual: {params['visual']['pattern']} pattern at {params['visual']['brightness']*100:.0f}% brightness")
    
    # Cooldown phase
    print("\n== Cooldown Phase ==")
    state = controller.update_physiological_state(
        heart_rate=120, 
        emg_activity=0.5,
        gsr=0.6,
        acceleration=0.8,
        impedance_data=470
    )
    params = controller.adjust_stimulation()
    print(f"Phase: {state['phase'].name}, Fatigue: {state['fatigue']:.2f}")
    print(f"TENS: {params['tens']['frequency']}Hz at {params['tens']['intensity']*100:.0f}% intensity")
    print(f"Visual: {params['visual']['pattern']} pattern at {params['visual']['brightness']*100:.0f}% brightness")
    
    # Recovery phase
    print("\n== Recovery Phase ==")
    state = controller.update_physiological_state(
        heart_rate=90, 
        emg_activity=0.2,
        gsr=0.3,
        acceleration=0.2,
        impedance_data=490
    )
    params = controller.adjust_stimulation()
    print(f"Phase: {state['phase'].name}, Fatigue: {state['fatigue']:.2f}")
    print(f"TENS: {params['tens']['frequency']}Hz at {params['tens']['intensity']*100:.0f}% intensity")
    print(f"Visual: {params['visual']['pattern']} pattern at {params['visual']['brightness']*100:.0f}% brightness")
