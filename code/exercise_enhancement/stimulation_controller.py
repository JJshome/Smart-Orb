#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Orb Exercise Enhancement - Stimulation Controller

This module implements the real-time control logic for the Smart Orb exercise
enhancement system. It handles sensor data processing, exercise detection,
and adaptive stimulation parameter adjustment during workouts.
"""

import time
import numpy as np
import json
import os
import joblib
from typing import Dict, List, Tuple, Optional, Union, Any
from enum import Enum


class ExercisePhase(Enum):
    """Enum representing different phases of an exercise session."""
    SETUP = 0
    WARMUP = 1
    MAIN = 2
    COOLDOWN = 3
    RECOVERY = 4


class ExerciseType(Enum):
    """Enum representing different exercise categories."""
    STRENGTH = 0
    ENDURANCE = 1
    HIIT = 2
    FLEXIBILITY = 3
    UNKNOWN = 4


class SmartOrbStimulationController:
    """
    Real-time controller for Smart Orb exercise enhancement stimulation.
    
    This class handles sensor data processing, exercise detection and tracking,
    and adaptive stimulation control to optimize workout performance.
    """
    
    def __init__(self, models_dir: str = "models", 
                 user_profile: Optional[Dict] = None):
        """
        Initialize the stimulation controller.
        
        Args:
            models_dir: Directory containing trained models
            user_profile: User profile data (optional, can be set later)
        """
        self.models_dir = models_dir
        self.user_profile = user_profile
        self.models = {}
        
        # Session state
        self.session_active = False
        self.session_id = None
        self.session_start_time = None
        self.session_data = []
        self.current_phase = ExercisePhase.SETUP
        self.detected_exercise_type = ExerciseType.UNKNOWN
        self.detected_exercise_name = None
        self.detected_intensity = None
        self.rep_count = 0
        self.last_rep_time = 0
        
        # Stimulation parameters
        self.base_stimulation_params = None
        self.current_stimulation_params = None
        self.stimulation_active = False
        
        # Load models if directory exists
        if os.path.exists(models_dir):
            self._load_models()
    
    def set_user_profile(self, user_profile: Dict) -> None:
        """
        Set or update the user profile.
        
        Args:
            user_profile: User profile data
        """
        self.user_profile = user_profile
        print(f"User profile updated for {user_profile.get('name', 'unknown user')}")
    
    def start_session(self, exercise_type: Optional[str] = None, 
                     intensity: Optional[str] = None) -> Dict:
        """
        Start a new exercise session.
        
        Args:
            exercise_type: Type of exercise (optional, can be auto-detected)
            intensity: Exercise intensity (optional, can be auto-detected)
            
        Returns:
            Session information dictionary
        """
        if self.session_active:
            return {"error": "Session already in progress"}
        
        if self.user_profile is None:
            return {"error": "User profile not set"}
        
        # Generate session ID
        self.session_id = f"session_{int(time.time())}"
        self.session_start_time = time.time()
        self.session_data = []
        self.current_phase = ExercisePhase.SETUP
        self.rep_count = 0
        self.last_rep_time = 0
        
        # Set exercise type if provided
        if exercise_type is not None:
            self.detected_exercise_name = exercise_type
            self.detected_exercise_type = self._get_exercise_category(exercise_type)
        
        # Set intensity if provided
        if intensity is not None:
            self.detected_intensity = intensity
        
        # Initialize stimulation parameters if both exercise type and intensity are known
        if self.detected_exercise_name is not None and self.detected_intensity is not None:
            self._initialize_stimulation_parameters()
        
        self.session_active = True
        
        return {
            "session_id": self.session_id,
            "start_time": self.session_start_time,
            "exercise_type": self.detected_exercise_name,
            "intensity": self.detected_intensity,
            "status": "active",
            "message": "Session started successfully"
        }
    
    def end_session(self) -> Dict:
        """
        End the current exercise session.
        
        Returns:
            Session summary dictionary
        """
        if not self.session_active:
            return {"error": "No active session"}
        
        # Compile session summary
        session_duration = time.time() - self.session_start_time
        
        # Calculate session metrics
        metrics = self._calculate_session_metrics()
        
        # Create session summary
        summary = {
            "session_id": self.session_id,
            "start_time": self.session_start_time,
            "end_time": time.time(),
            "duration_seconds": session_duration,
            "exercise_type": self.detected_exercise_name,
            "intensity": self.detected_intensity,
            "stimulation_active": self.stimulation_active,
            "metrics": metrics
        }
        
        # Reset session state
        self.session_active = False
        self.stimulation_active = False
        self.current_stimulation_params = None
        
        # Save session data
        self._save_session_data(summary)
        
        return summary
    
    def process_sensor_data(self, sensor_data: Dict) -> Dict:
        """
        Process incoming sensor data and update stimulation parameters.
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Dictionary with processing results and stimulation parameters
        """
        if not self.session_active:
            return {"error": "No active session"}
        
        # Add timestamp if not present
        if "timestamp" not in sensor_data:
            sensor_data["timestamp"] = time.time()
        
        # Add to session data
        self.session_data.append(sensor_data)
        
        # Extract relevant data
        heart_rate = sensor_data.get("heart_rate")
        emg_primary = sensor_data.get("emg_primary")
        accel_data = (
            sensor_data.get("accel_x"),
            sensor_data.get("accel_y"),
            sensor_data.get("accel_z")
        )
        
        # Detect exercise type and intensity if not already known
        if self.detected_exercise_type == ExerciseType.UNKNOWN:
            self._detect_exercise_type(sensor_data)
        
        if self.detected_intensity is None:
            self._detect_intensity(sensor_data)
        
        # Initialize stimulation parameters if needed
        if (self.current_stimulation_params is None and 
                self.detected_exercise_name is not None and 
                self.detected_intensity is not None):
            self._initialize_stimulation_parameters()
        
        # Update session phase
        self._update_session_phase(sensor_data)
        
        # Detect and count repetitions for applicable exercises
        if self._is_rep_based_exercise():
            new_reps = self._detect_repetitions(sensor_data)
            if new_reps > 0:
                self.rep_count += new_reps
                self.last_rep_time = sensor_data.get("timestamp", time.time())
        
        # Adapt stimulation parameters based on current state
        if self.stimulation_active and self.current_stimulation_params is not None:
            self._adapt_stimulation_parameters(sensor_data)
        
        # Prepare response
        response = {
            "timestamp": sensor_data.get("timestamp"),
            "session_id": self.session_id,
            "exercise_type": self.detected_exercise_name,
            "intensity": self.detected_intensity,
            "session_phase": self.current_phase.name,
            "elapsed_time": time.time() - self.session_start_time
        }
        
        # Add exercise-specific metrics
        if self._is_rep_based_exercise():
            response["rep_count"] = self.rep_count
        
        # Add stimulation parameters if active
        if self.stimulation_active:
            response["stimulation"] = self.current_stimulation_params
        
        return response
    
    def toggle_stimulation(self, enable: bool) -> Dict:
        """
        Enable or disable stimulation.
        
        Args:
            enable: Whether to enable or disable stimulation
            
        Returns:
            Dictionary with updated stimulation state
        """
        if not self.session_active:
            return {"error": "No active session"}
        
        if enable and self.detected_exercise_name is None:
            return {"error": "Cannot enable stimulation: Exercise type unknown"}
        
        if enable and self.detected_intensity is None:
            return {"error": "Cannot enable stimulation: Exercise intensity unknown"}
        
        if enable and self.current_stimulation_params is None:
            self._initialize_stimulation_parameters()
        
        self.stimulation_active = enable
        
        return {
            "stimulation_active": self.stimulation_active,
            "stimulation_params": self.current_stimulation_params if self.stimulation_active else None
        }
    
    def adjust_stimulation(self, adjustment: Dict) -> Dict:
        """
        Manually adjust stimulation parameters.
        
        Args:
            adjustment: Dictionary with parameter adjustments
            
        Returns:
            Dictionary with updated stimulation parameters
        """
        if not self.session_active:
            return {"error": "No active session"}
        
        if not self.stimulation_active:
            return {"error": "Stimulation not active"}
        
        if self.current_stimulation_params is None:
            return {"error": "Stimulation parameters not initialized"}
        
        # Apply adjustments
        if "tens_intensity" in adjustment:
            # Ensure intensity stays within safe limits
            new_intensity = adjustment["tens_intensity"]
            new_intensity = min(10, max(1, new_intensity))  # 1-10 mA range
            
            self.current_stimulation_params["tens_params"]["intensity"] = new_intensity
        
        if "tens_frequency" in adjustment:
            # Ensure frequency stays within reasonable limits
            new_frequency = adjustment["tens_frequency"]
            new_frequency = min(100, max(1, new_frequency))  # 1-100 Hz range
            
            self.current_stimulation_params["tens_params"]["frequency"] = new_frequency
        
        if "target_muscles" in adjustment:
            self.current_stimulation_params["tens_params"]["target_muscles"] = adjustment["target_muscles"]
        
        # Sensory adjustments
        for sensory_type in ["visual", "audio", "haptic", "thermal"]:
            if f"{sensory_type}_intensity" in adjustment:
                new_intensity = adjustment[f"{sensory_type}_intensity"]
                new_intensity = min(1.0, max(0.0, new_intensity))  # 0-1 range
                
                self.current_stimulation_params["sensory_params"][sensory_type]["intensity"] = new_intensity
        
        return {"stimulation_params": self.current_stimulation_params}
    
    def _load_models(self) -> None:
        """
        Load trained models from disk.
        """
        print(f"Loading models from {self.models_dir}...")
        
        # Find all model files
        model_files = [f for f in os.listdir(self.models_dir) if f.endswith(".joblib")]
        
        # Load each model
        for model_file in model_files:
            model_name = model_file.replace(".joblib", "")
            model_path = os.path.join(self.models_dir, model_file)
            
            try:
                model = joblib.load(model_path)
                self.models[model_name] = model
            except Exception as e:
                print(f"Error loading model {model_file}: {e}")
        
        print(f"Loaded {len(self.models)} models")
    
    def _get_exercise_category(self, exercise_type: str) -> ExerciseType:
        """
        Determine the exercise category for a given exercise type.
        
        Args:
            exercise_type: Exercise type name
            
        Returns:
            ExerciseType enum value
        """
        strength_exercises = ["squat", "deadlift", "bench_press", "shoulder_press"]
        endurance_exercises = ["running", "cycling", "swimming", "rowing"]
        hiit_exercises = ["jumping_jacks", "burpees", "mountain_climbers"]
        flexibility_exercises = ["yoga", "pilates", "stretching"]
        
        if exercise_type in strength_exercises:
            return ExerciseType.STRENGTH
        elif exercise_type in endurance_exercises:
            return ExerciseType.ENDURANCE
        elif exercise_type in hiit_exercises:
            return ExerciseType.HIIT
        elif exercise_type in flexibility_exercises:
            return ExerciseType.FLEXIBILITY
        else:
            return ExerciseType.UNKNOWN
    
    def _detect_exercise_type(self, sensor_data: Dict) -> None:
        """
        Detect exercise type from sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        """
        # In a real implementation, this would use a machine learning model
        # to classify the exercise type based on patterns in the sensor data
        
        # Simplified implementation using acceleration patterns
        if "accel_x" in sensor_data and "accel_y" in sensor_data and "accel_z" in sensor_data:
            accel_x = sensor_data["accel_x"]
            accel_y = sensor_data["accel_y"]
            accel_z = sensor_data["accel_z"]
            
            # Check for repetitive vertical movement (e.g., squats, deadlifts)
            if len(self.session_data) > 10 and "accel_z" in self.session_data[0]:
                accel_z_history = [d.get("accel_z", 0) for d in self.session_data[-10:]]
                z_variation = np.std(accel_z_history)
                
                if z_variation > 1.0 and abs(accel_z) > 10.0:
                    self.detected_exercise_name = "squat"  # Simplified example
                    self.detected_exercise_type = ExerciseType.STRENGTH
                    return
            
            # Check for continuous rhythmic movement (e.g., running, cycling)
            if len(self.session_data) > 30:
                accel_norm_history = [
                    np.sqrt(d.get("accel_x", 0)**2 + d.get("accel_y", 0)**2 + d.get("accel_z", 0)**2)
                    for d in self.session_data[-30:]
                ]
                
                # Check for periodic pattern
                if self._detect_periodicity(accel_norm_history, 0.5, 2.0):  # 0.5-2.0 Hz range
                    self.detected_exercise_name = "running"  # Simplified example
                    self.detected_exercise_type = ExerciseType.ENDURANCE
                    return
        
        # If we have enough data and still haven't detected the exercise type,
        # default to a common exercise type based on most likely pattern
        if len(self.session_data) > 60 and self.detected_exercise_type == ExerciseType.UNKNOWN:
            heart_rate_history = [d.get("heart_rate", 0) for d in self.session_data[-30:] if "heart_rate" in d]
            
            if heart_rate_history and np.mean(heart_rate_history) > 120:
                self.detected_exercise_name = "running"  # High HR suggests cardio
                self.detected_exercise_type = ExerciseType.ENDURANCE
            else:
                self.detected_exercise_name = "squat"  # Default to strength
                self.detected_exercise_type = ExerciseType.STRENGTH
    
    def _detect_intensity(self, sensor_data: Dict) -> None:
        """
        Detect exercise intensity from sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        """
        # In a real implementation, this would use heart rate, power output,
        # and other metrics to determine the exercise intensity
        
        # Simplified implementation using heart rate
        if "heart_rate" in sensor_data and self.user_profile is not None:
            heart_rate = sensor_data["heart_rate"]
            max_hr = self.user_profile.get("physiological", {}).get("max_hr", 220 - self.user_profile.get("age", 30))
            hr_percentage = heart_rate / max_hr
            
            if hr_percentage < 0.6:
                self.detected_intensity = "low"
            elif hr_percentage < 0.7:
                self.detected_intensity = "moderate"
            elif hr_percentage < 0.85:
                self.detected_intensity = "high"
            else:
                self.detected_intensity = "very_high"
            
            return
        
        # If heart rate not available, use power output
        if "power_output" in sensor_data:
            power = sensor_data["power_output"]
            
            # These thresholds would normally be calibrated to the user
            if power < 50:
                self.detected_intensity = "low"
            elif power < 100:
                self.detected_intensity = "moderate"
            elif power < 150:
                self.detected_intensity = "high"
            else:
                self.detected_intensity = "very_high"
            
            return
        
        # Default value if no reliable indicators available
        if self.detected_intensity is None and len(self.session_data) > 30:
            self.detected_intensity = "moderate"
    
    def _initialize_stimulation_parameters(self) -> None:
        """
        Initialize stimulation parameters based on detected exercise type and intensity.
        """
        if self.detected_exercise_name is None or self.detected_intensity is None:
            return
        
        # Determine exercise category
        category = self._get_exercise_category(self.detected_exercise_name).name.lower()
        if category == "unknown":
            category = "strength"  # Default to strength if unknown
        
        # In a real implementation, this would use a machine learning model to
        # predict optimal stimulation parameters based on the user profile and
        # exercise characteristics
        
        # Simplified implementation with exercise category-specific defaults
        if category == "strength":
            # Base parameters for strength exercises
            self.base_stimulation_params = {
                "mode": "strength_enhancement",
                "tens_params": {
                    "frequency": 2,  # Hz
                    "pulse_width": 300,  # μs
                    "intensity": 7,  # mA
                    "waveform": "biphasic_rectangular",
                    "target_muscles": self._get_target_muscles(self.detected_exercise_name)
                },
                "sensory_params": {
                    "visual": {
                        "color": "red",
                        "pattern": "pulse",
                        "frequency": 10,  # Hz
                        "intensity": 0.7
                    },
                    "audio": {
                        "type": "binaural",
                        "frequency": 15,  # Hz
                        "volume": 0.6,
                        "intensity": 0.6
                    },
                    "haptic": {
                        "pattern": "rhythmic",
                        "frequency": 150,  # Hz
                        "intensity": 0.7
                    },
                    "thermal": {
                        "mode": "warm",
                        "temperature": 33,  # °C
                        "intensity": 0.8
                    }
                }
            }
        elif category == "endurance":
            # Base parameters for endurance exercises
            self.base_stimulation_params = {
                "mode": "endurance_enhancement",
                "tens_params": {
                    "frequency": 10,  # Hz
                    "pulse_width": 250,  # μs
                    "intensity": 6,  # mA
                    "waveform": "biphasic_sinusoidal",
                    "target_muscles": self._get_target_muscles(self.detected_exercise_name)
                },
                "sensory_params": {
                    "visual": {
                        "color": "yellow",
                        "pattern": "steady_pulse",
                        "frequency": 5,  # Hz
                        "intensity": 0.6
                    },
                    "audio": {
                        "type": "rhythmic",
                        "beat_frequency": 130,  # BPM
                        "volume": 0.5,
                        "intensity": 0.5
                    },
                    "haptic": {
                        "pattern": "rhythm_match",
                        "frequency": 100,  # Hz
                        "intensity": 0.6
                    },
                    "thermal": {
                        "mode": "cool",
                        "temperature": 30,  # °C
                        "intensity": 0.7
                    }
                }
            }
        elif category == "hiit":
            # Base parameters for HIIT exercises
            self.base_stimulation_params = {
                "mode": "hiit_enhancement",
                "tens_params": {
                    "frequency": 8,  # Hz
                    "pulse_width": 275,  # μs
                    "intensity": 7,  # mA
                    "waveform": "biphasic_asymmetrical",
                    "target_muscles": self._get_target_muscles(self.detected_exercise_name)
                },
                "sensory_params": {
                    "visual": {
                        "color": "green",
                        "pattern": "interval_pulse",
                        "work_frequency": 15,  # Hz
                        "rest_frequency": 5,  # Hz
                        "intensity": 0.7
                    },
                    "audio": {
                        "type": "interval",
                        "work_beat": 140,  # BPM
                        "rest_beat": 90,  # BPM
                        "volume": 0.7,
                        "intensity": 0.7
                    },
                    "haptic": {
                        "pattern": "interval",
                        "work_frequency": 180,  # Hz
                        "rest_frequency": 60,  # Hz
                        "intensity": 0.8
                    },
                    "thermal": {
                        "mode": "alternating",
                        "work_temp": 31,  # °C
                        "rest_temp": 28,  # °C
                        "intensity": 0.7
                    }
                }
            }
        else:  # flexibility
            # Base parameters for flexibility exercises
            self.base_stimulation_params = {
                "mode": "flexibility_enhancement",
                "tens_params": {
                    "frequency": 3,  # Hz
                    "pulse_width": 200,  # μs
                    "intensity": 5,  # mA
                    "waveform": "biphasic_symmetrical",
                    "target_muscles": self._get_target_muscles(self.detected_exercise_name)
                },
                "sensory_params": {
                    "visual": {
                        "color": "blue",
                        "pattern": "slow_wave",
                        "frequency": 3,  # Hz
                        "intensity": 0.5
                    },
                    "audio": {
                        "type": "binaural",
                        "frequency": 8,  # Hz
                        "volume": 0.4,
                        "intensity": 0.4
                    },
                    "haptic": {
                        "pattern": "wave",
                        "frequency": 80,  # Hz
                        "intensity": 0.5
                    },
                    "thermal": {
                        "mode": "warm",
                        "temperature": 32,  # °C
                        "intensity": 0.6
                    }
                }
            }
        
        # Adjust parameters based on intensity
        intensity_factor = {
            "low": 0.7,
            "moderate": 0.85,
            "high": 1.0,
            "very_high": 1.15
        }.get(self.detected_intensity, 0.85)
        
        # Adjust TENS intensity
        self.base_stimulation_params["tens_params"]["intensity"] *= intensity_factor
        
        # Adjust TENS pulse width
        self.base_stimulation_params["tens_params"]["pulse_width"] = int(
            self.base_stimulation_params["tens_params"]["pulse_width"] * intensity_factor
        )
        
        # Adjust sensory intensities
        for sensory_type in self.base_stimulation_params["sensory_params"]:
            if "intensity" in self.base_stimulation_params["sensory_params"][sensory_type]:
                self.base_stimulation_params["sensory_params"][sensory_type]["intensity"] *= intensity_factor
        
        # Further adjust based on user profile if available
        if self.user_profile is not None and "stimulation_response" in self.user_profile:
            stim_response = self.user_profile["stimulation_response"]
            
            # Adjust for TENS sensitivity
            tens_sensitivity = stim_response.get("tens_sensitivity", 1.0)
            self.base_stimulation_params["tens_params"]["intensity"] /= tens_sensitivity
            
            # Use preferred frequency if appropriate
            preferred_frequency = stim_response.get("preferred_frequency", 50)
            
            # Only use preferred frequency if it's in a reasonable range for the exercise category
            if category == "strength" and 2 <= preferred_frequency <= 5:
                self.base_stimulation_params["tens_params"]["frequency"] = preferred_frequency
            elif category == "endurance" and 8 <= preferred_frequency <= 20:
                self.base_stimulation_params["tens_params"]["frequency"] = preferred_frequency
            elif category == "hiit" and 5 <= preferred_frequency <= 15:
                self.base_stimulation_params["tens_params"]["frequency"] = preferred_frequency
            elif category == "flexibility" and 2 <= preferred_frequency <= 10:
                self.base_stimulation_params["tens_params"]["frequency"] = preferred_frequency
        
        # Ensure parameters are within safe limits
        self.base_stimulation_params["tens_params"]["intensity"] = min(
            10, max(1, self.base_stimulation_params["tens_params"]["intensity"])
        )
        
        # Clone base parameters to current parameters
        self.current_stimulation_params = self._clone_params(self.base_stimulation_params)
    
    def _update_session_phase(self, sensor_data: Dict) -> None:
        """
        Update the exercise session phase based on elapsed time and sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        """
        # Calculate elapsed time
        elapsed_time = sensor_data.get("timestamp", time.time()) - self.session_start_time
        
        # Determine phase based on elapsed time and session data
        if self.current_phase == ExercisePhase.SETUP:
            # Transition from setup to warmup once we have enough data
            if len(self.session_data) > 10:
                self.current_phase = ExercisePhase.WARMUP
        
        elif self.current_phase == ExercisePhase.WARMUP:
            # Transition from warmup to main once heart rate is elevated
            if len(self.session_data) > 30:
                recent_hr = [d.get("heart_rate", 0) for d in self.session_data[-10:] if "heart_rate" in d]
                
                if recent_hr and np.mean(recent_hr) > 100:  # Simplified threshold
                    self.current_phase = ExercisePhase.MAIN
            
            # Time-based fallback (transition after 5 minutes)
            if elapsed_time > 5 * 60:
                self.current_phase = ExercisePhase.MAIN
        
        elif self.current_phase == ExercisePhase.MAIN:
            # Transition from main to cooldown based on various factors
            
            # Time-based: if session has been going for a while
            if elapsed_time > 45 * 60:  # 45 minutes
                self.current_phase = ExercisePhase.COOLDOWN
                return
            
            # Heart rate based: if heart rate is decreasing
            if len(self.session_data) > 60:
                recent_hr = [d.get("heart_rate", 0) for d in self.session_data[-30:] if "heart_rate" in d]
                earlier_hr = [d.get("heart_rate", 0) for d in self.session_data[-60:-30] if "heart_rate" in d]
                
                if recent_hr and earlier_hr and np.mean(recent_hr) < np.mean(earlier_hr) * 0.9:
                    self.current_phase = ExercisePhase.COOLDOWN
                    return
            
            # Activity based: if activity level is decreasing
            if len(self.session_data) > 60:
                recent_activity = [self._calculate_activity_level(d) for d in self.session_data[-30:]]
                earlier_activity = [self._calculate_activity_level(d) for d in self.session_data[-60:-30]]
                
                if np.mean(recent_activity) < np.mean(earlier_activity) * 0.7:
                    self.current_phase = ExercisePhase.COOLDOWN
                    return
        
        elif self.current_phase == ExercisePhase.COOLDOWN:
            # Transition from cooldown to recovery once heart rate and activity are low
            if len(self.session_data) > 30:
                recent_hr = [d.get("heart_rate", 0) for d in self.session_data[-10:] if "heart_rate" in d]
                recent_activity = [self._calculate_activity_level(d) for d in self.session_data[-10:]]
                
                if (recent_hr and np.mean(recent_hr) < 100 and 
                        np.mean(recent_activity) < 0.3):  # Simplified thresholds
                    self.current_phase = ExercisePhase.RECOVERY
            
            # Time-based fallback (transition after 5 minutes of cooldown)
            if self.current_phase == ExercisePhase.COOLDOWN and elapsed_time > 5 * 60:
                phase_start_time = next((d.get("timestamp", 0) for d in reversed(self.session_data) 
                                        if d.get("session_phase") != ExercisePhase.COOLDOWN.name), 0)
                
                if phase_start_time > 0 and (time.time() - phase_start_time) > 5 * 60:
                    self.current_phase = ExercisePhase.RECOVERY
    
    def _detect_repetitions(self, sensor_data: Dict) -> int:
        """
        Detect exercise repetitions from sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Number of newly detected repetitions
        """
        # This would normally use a machine learning model or signal processing
        # to detect repetitions based on acceleration patterns, EMG, etc.
        
        # Simplified implementation using acceleration threshold crossing
        if "accel_z" in sensor_data and self.detected_exercise_type == ExerciseType.STRENGTH:
            # For strength exercises, look for large vertical acceleration changes
            if len(self.session_data) < 2:
                return 0
            
            current_z = sensor_data["accel_z"]
            previous_z = self.session_data[-2].get("accel_z", current_z)
            
            # Detect zero crossing with sufficient magnitude
            if previous_z < 0 and current_z > 2.0:
                # Check if enough time has passed since last rep
                current_time = sensor_data.get("timestamp", time.time())
                if current_time - self.last_rep_time > 1.0:  # At least 1 second between reps
                    return 1
        
        # For HIIT exercises, use a different detection strategy
        if self.detected_exercise_type == ExerciseType.HIIT:
            # For simplified implementation, use an energy-based approach
            if "accel_x" in sensor_data and "accel_y" in sensor_data and "accel_z" in sensor_data:
                accel_norm = np.sqrt(sensor_data["accel_x"]**2 + 
                                  sensor_data["accel_y"]**2 + 
                                  sensor_data["accel_z"]**2)
                
                if len(self.session_data) < 5:
                    return 0
                
                # Calculate recent average energy
                recent_norms = [np.sqrt(d.get("accel_x", 0)**2 + 
                                      d.get("accel_y", 0)**2 + 
                                      d.get("accel_z", 0)**2) 
                              for d in self.session_data[-5:]]
                avg_norm = np.mean(recent_norms)
                
                # Check for energy spike
                if accel_norm > avg_norm * 1.5 and accel_norm > 15.0:
                    # Check if enough time has passed since last rep
                    current_time = sensor_data.get("timestamp", time.time())
                    if current_time - self.last_rep_time > 0.5:  # At least 0.5 seconds between reps
                        return 1
        
        return 0
    
    def _adapt_stimulation_parameters(self, sensor_data: Dict) -> None:
        """
        Adapt stimulation parameters based on current session phase and sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
        """
        if self.current_stimulation_params is None:
            return
        
        # Phase-specific adaptations
        if self.current_phase == ExercisePhase.WARMUP:
            # During warmup, use gentler stimulation
            self.current_stimulation_params["tens_params"]["intensity"] = \
                self.base_stimulation_params["tens_params"]["intensity"] * 0.7
            
            # Reduce pulse width
            self.current_stimulation_params["tens_params"]["pulse_width"] = \
                int(self.base_stimulation_params["tens_params"]["pulse_width"] * 0.8)
            
            # Adjust sensory parameters
            for sensory_type in self.current_stimulation_params["sensory_params"]:
                if "intensity" in self.current_stimulation_params["sensory_params"][sensory_type]:
                    self.current_stimulation_params["sensory_params"][sensory_type]["intensity"] = \
                        self.base_stimulation_params["sensory_params"][sensory_type]["intensity"] * 0.8
        
        elif self.current_phase == ExercisePhase.MAIN:
            # During main exercise, adapt based on intensity and fatigue
            
            # Reset to base parameters
            self.current_stimulation_params = self._clone_params(self.base_stimulation_params)
            
            # Calculate fatigue level (simplified)
            fatigue_level = self._estimate_fatigue_level(sensor_data)
            
            # Adjust for fatigue - increase stimulation as fatigue increases
            fatigue_factor = 1.0 + (fatigue_level * 0.2)  # Up to 20% increase
            
            # Increase TENS intensity with fatigue (within limits)
            tens_intensity = self.base_stimulation_params["tens_params"]["intensity"] * fatigue_factor
            self.current_stimulation_params["tens_params"]["intensity"] = min(10, tens_intensity)
            
            # For HIIT exercises, adapt based on work/rest cycles
            if self.detected_exercise_type == ExerciseType.HIIT:
                # Detect if in work or rest phase
                in_work_phase = self._detect_hiit_work_phase(sensor_data)
                
                if in_work_phase:
                    # During work phase, increase stimulation
                    self.current_stimulation_params["tens_params"]["intensity"] *= 1.1
                    
                    # Use work-specific sensory parameters
                    if "work_frequency" in self.current_stimulation_params["sensory_params"]["visual"]:
                        self.current_stimulation_params["sensory_params"]["visual"]["frequency"] = \
                            self.current_stimulation_params["sensory_params"]["visual"]["work_frequency"]
                    
                    if "work_beat" in self.current_stimulation_params["sensory_params"]["audio"]:
                        self.current_stimulation_params["sensory_params"]["audio"]["beat_frequency"] = \
                            self.current_stimulation_params["sensory_params"]["audio"]["work_beat"]
                else:
                    # During rest phase, decrease stimulation
                    self.current_stimulation_params["tens_params"]["intensity"] *= 0.7
                    
                    # Use rest-specific sensory parameters
                    if "rest_frequency" in self.current_stimulation_params["sensory_params"]["visual"]:
                        self.current_stimulation_params["sensory_params"]["visual"]["frequency"] = \
                            self.current_stimulation_params["sensory_params"]["visual"]["rest_frequency"]
                    
                    if "rest_beat" in self.current_stimulation_params["sensory_params"]["audio"]:
                        self.current_stimulation_params["sensory_params"]["audio"]["beat_frequency"] = \
                            self.current_stimulation_params["sensory_params"]["audio"]["rest_beat"]
            
            # For strength exercises, adapt based on rep detection
            elif self.detected_exercise_type == ExerciseType.STRENGTH and self._is_rep_based_exercise():
                # Time since last rep
                time_since_last_rep = sensor_data.get("timestamp", time.time()) - self.last_rep_time
                
                # If recently performed a rep, increase stimulation temporarily
                if time_since_last_rep < 2.0:  # Within 2 seconds of a rep
                    self.current_stimulation_params["tens_params"]["intensity"] *= 1.2
                    
                    # Pulse width increases for stronger contraction
                    self.current_stimulation_params["tens_params"]["pulse_width"] = int(
                        self.current_stimulation_params["tens_params"]["pulse_width"] * 1.1
                    )
        
        elif self.current_phase == ExercisePhase.COOLDOWN:
            # During cooldown, gradually reduce stimulation
            intensity_factor = 0.6  # 60% of base intensity
            
            # Calculate time in cooldown phase
            phase_start_time = next((d.get("timestamp", self.session_start_time) 
                                   for d in reversed(self.session_data) 
                                   if d.get("session_phase") != ExercisePhase.COOLDOWN.name), 
                                  self.session_start_time)
            time_in_phase = sensor_data.get("timestamp", time.time()) - phase_start_time
            
            # Further reduce stimulation over time
            if time_in_phase > 60:  # After 1 minute in cooldown
                intensity_factor = 0.4
            if time_in_phase > 180:  # After 3 minutes in cooldown
                intensity_factor = 0.2
            
            # Apply intensity factor
            self.current_stimulation_params["tens_params"]["intensity"] = \
                self.base_stimulation_params["tens_params"]["intensity"] * intensity_factor
            
            # Change TENS parameters for recovery support
            self.current_stimulation_params["tens_params"]["frequency"] = 100  # Higher frequency for recovery
            self.current_stimulation_params["tens_params"]["pulse_width"] = 200  # Standard pulse width
            
            # Adjust sensory parameters for relaxation
            self.current_stimulation_params["sensory_params"]["visual"]["color"] = "blue"
            self.current_stimulation_params["sensory_params"]["visual"]["pattern"] = "slow_wave"
            self.current_stimulation_params["sensory_params"]["visual"]["frequency"] = 2
            
            self.current_stimulation_params["sensory_params"]["audio"]["type"] = "binaural"
            self.current_stimulation_params["sensory_params"]["audio"]["frequency"] = 10
            
            self.current_stimulation_params["sensory_params"]["haptic"]["pattern"] = "wave"
            self.current_stimulation_params["sensory_params"]["haptic"]["frequency"] = 60
        
        elif self.current_phase == ExercisePhase.RECOVERY:
            # During recovery, use specialized recovery stimulation
            self.current_stimulation_params["mode"] = "recovery"
            self.current_stimulation_params["tens_params"]["frequency"] = 100  # Higher frequency for recovery
            self.current_stimulation_params["tens_params"]["pulse_width"] = 200  # Standard pulse width
            self.current_stimulation_params["tens_params"]["intensity"] = \
                self.base_stimulation_params["tens_params"]["intensity"] * 0.3  # 30% intensity
            
            # Complete relaxation sensory profile
            self.current_stimulation_params["sensory_params"]["visual"]["color"] = "blue"
            self.current_stimulation_params["sensory_params"]["visual"]["pattern"] = "slow_fade"
            self.current_stimulation_params["sensory_params"]["visual"]["frequency"] = 1
            self.current_stimulation_params["sensory_params"]["visual"]["intensity"] = 0.3
            
            self.current_stimulation_params["sensory_params"]["audio"]["type"] = "binaural"
            self.current_stimulation_params["sensory_params"]["audio"]["frequency"] = 6
            self.current_stimulation_params["sensory_params"]["audio"]["volume"] = 0.3
            
            self.current_stimulation_params["sensory_params"]["haptic"]["pattern"] = "gentle_wave"
            self.current_stimulation_params["sensory_params"]["haptic"]["frequency"] = 40
            self.current_stimulation_params["sensory_params"]["haptic"]["intensity"] = 0.3
            
            self.current_stimulation_params["sensory_params"]["thermal"]["mode"] = "warm"
            self.current_stimulation_params["sensory_params"]["thermal"]["temperature"] = 34
            self.current_stimulation_params["sensory_params"]["thermal"]["intensity"] = 0.7
        
        # Ensure parameters are within safe limits
        self._apply_safety_limits()
    
    def _is_rep_based_exercise(self) -> bool:
        """
        Determine if the current exercise is rep-based (e.g., strength, HIIT).
        
        Returns:
            True if the exercise is rep-based, False otherwise
        """
        return (self.detected_exercise_type == ExerciseType.STRENGTH or 
                self.detected_exercise_type == ExerciseType.HIIT)
    
    def _calculate_activity_level(self, sensor_data: Dict) -> float:
        """
        Calculate activity level from sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Activity level (0-1 scale)
        """
        # Use acceleration magnitude as a proxy for activity level
        if all(k in sensor_data for k in ["accel_x", "accel_y", "accel_z"]):
            accel_norm = np.sqrt(sensor_data["accel_x"]**2 + 
                              sensor_data["accel_y"]**2 + 
                              sensor_data["accel_z"]**2)
            
            # Normalize to 0-1 scale (assuming typical range 0-20 m/s²)
            activity = min(1.0, accel_norm / 20.0)
            return activity
        
        # Fallback if accelerometer data not available
        if "heart_rate" in sensor_data and self.user_profile is not None:
            heart_rate = sensor_data["heart_rate"]
            max_hr = self.user_profile.get("physiological", {}).get("max_hr", 220 - self.user_profile.get("age", 30))
            resting_hr = self.user_profile.get("physiological", {}).get("resting_hr", 60)
            
            # Normalize heart rate to 0-1 scale
            if max_hr > resting_hr:  # Avoid division by zero
                activity = (heart_rate - resting_hr) / (max_hr - resting_hr)
                activity = max(0.0, min(1.0, activity))  # Clamp to 0-1 range
                return activity
        
        # Default value if no activity indicators available
        return 0.5
    
    def _estimate_fatigue_level(self, sensor_data: Dict) -> float:
        """
        Estimate fatigue level from sensor data.
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            Fatigue level (0-1 scale)
        """
        # In a real implementation, this would use various physiological indicators
        # such as EMG frequency shift, heart rate drift, power output decline, etc.
        
        # Simplified implementation based on session duration and heart rate
        elapsed_time = sensor_data.get("timestamp", time.time()) - self.session_start_time
        normalized_time = min(1.0, elapsed_time / (60 * 60))  # Normalize to 0-1 over 1 hour
        
        # Base fatigue on elapsed time
        fatigue = normalized_time * 0.7  # Time contributes 70% to fatigue estimate
        
        # Add heart rate component if available
        if "heart_rate" in sensor_data and len(self.session_data) > 30:
            current_hr = sensor_data["heart_rate"]
            
            # Compare to heart rate from earlier in the session
            early_hr_data = [d.get("heart_rate", 0) for d in self.session_data[:10] if "heart_rate" in d]
            if early_hr_data:
                early_hr = np.mean(early_hr_data)
                
                # Calculate heart rate drift
                if early_hr > 0:  # Avoid division by zero
                    hr_drift = (current_hr - early_hr) / early_hr
                    hr_drift = max(0.0, min(0.3, hr_drift))  # Clamp to 0-0.3 range
                    
                    # Heart rate drift contributes 30% to fatigue estimate
                    fatigue = 0.7 * fatigue + 0.3 * (hr_drift / 0.3)
        
        return max(0.0, min(1.0, fatigue))  # Clamp to 0-1 range
    
    def _detect_hiit_work_phase(self, sensor_data: Dict) -> bool:
        """
        Detect if the current sensor data indicates a HIIT work phase.
        
        Args:
            sensor_data: Dictionary containing sensor readings
            
        Returns:
            True if in work phase, False if in rest phase
        """
        # For HIIT exercises, detect work/rest phases based on activity level
        if len(self.session_data) < 5:
            return True  # Default to work phase at the beginning
        
        # Calculate recent activity levels
        recent_activity = [self._calculate_activity_level(d) for d in self.session_data[-5:]]
        avg_activity = np.mean(recent_activity)
        
        # If average activity is above threshold, consider it a work phase
        return avg_activity > 0.5
    
    def _detect_periodicity(self, signal: List[float], min_freq: float, max_freq: float) -> bool:
        """
        Detect if a signal has periodic components in a specific frequency range.
        
        Args:
            signal: List of signal values
            min_freq: Minimum frequency to detect (Hz)
            max_freq: Maximum frequency to detect (Hz)
            
        Returns:
            True if periodicity detected, False otherwise
        """
        if len(signal) < 10:
            return False
        
        # Simple autocorrelation-based periodicity detection
        signal = np.array(signal)
        signal = signal - np.mean(signal)  # Remove mean
        
        # Calculate autocorrelation
        corr = np.correlate(signal, signal, mode='full')
        corr = corr[len(corr)//2:]  # Use only positive lags
        
        # Normalize
        corr = corr / np.max(corr)
        
        # Find peaks
        peaks = []
        for i in range(1, len(corr)-1):
            if corr[i] > corr[i-1] and corr[i] > corr[i+1] and corr[i] > 0.5:
                peaks.append(i)
        
        # Need at least one peak
        if not peaks:
            return False
        
        # Check if first peak is in frequency range
        if len(peaks) > 0:
            first_peak = peaks[0]
            if first_peak == 0:
                first_peak = peaks[1] if len(peaks) > 1 else 0
            
            if first_peak > 0:
                freq = 1.0 / first_peak  # Simplified frequency estimation
                return min_freq <= freq <= max_freq
        
        return False
    
    def _get_target_muscles(self, exercise_type: str) -> List[str]:
        """
        Get target muscles for a specific exercise type.
        
        Args:
            exercise_type: Type of exercise
            
        Returns:
            List of target muscle groups
        """
        muscle_targets = {
            "squat": ["quadriceps", "glutes", "hamstrings", "core"],
            "deadlift": ["hamstrings", "glutes", "lower_back", "upper_back"],
            "bench_press": ["pectorals", "triceps", "anterior_deltoids"],
            "shoulder_press": ["deltoids", "triceps", "upper_back"],
            "running": ["quadriceps", "hamstrings", "calves", "hip_flexors"],
            "cycling": ["quadriceps", "hamstrings", "glutes", "calves"],
            "swimming": ["lats", "pectorals", "deltoids", "triceps", "core"],
            "rowing": ["lats", "rhomboids", "biceps", "quadriceps", "hamstrings"],
            "jumping_jacks": ["deltoids", "quadriceps", "calves", "core"],
            "burpees": ["pectorals", "deltoids", "triceps", "quadriceps", "core"],
            "mountain_climbers": ["core", "hip_flexors", "shoulders", "quadriceps"],
            "yoga": ["core", "hip_flexors", "hamstrings", "shoulders"],
            "pilates": ["core", "glutes", "inner_thighs", "upper_back"],
            "stretching": ["hamstrings", "quadriceps", "hip_flexors", "chest", "shoulders"]
        }
        
        return muscle_targets.get(exercise_type, ["quadriceps", "hamstrings", "core"])
    
    def _clone_params(self, params: Dict) -> Dict:
        """
        Create a deep copy of parameter dictionary.
        
        Args:
            params: Parameter dictionary to clone
            
        Returns:
            Clone of the parameter dictionary
        """
        # Simple deep copy for JSON-serializable dictionaries
        return json.loads(json.dumps(params))
    
    def _apply_safety_limits(self) -> None:
        """
        Apply safety limits to all stimulation parameters.
        """
        if self.current_stimulation_params is None:
            return
        
        # TENS intensity limits
        self.current_stimulation_params["tens_params"]["intensity"] = min(
            10, max(1, self.current_stimulation_params["tens_params"]["intensity"])
        )
        
        # TENS frequency limits
        self.current_stimulation_params["tens_params"]["frequency"] = min(
            200, max(1, self.current_stimulation_params["tens_params"]["frequency"])
        )
        
        # TENS pulse width limits
        self.current_stimulation_params["tens_params"]["pulse_width"] = min(
            500, max(50, self.current_stimulation_params["tens_params"]["pulse_width"])
        )
        
        # Sensory intensity limits
        for sensory_type in self.current_stimulation_params["sensory_params"]:
            if "intensity" in self.current_stimulation_params["sensory_params"][sensory_type]:
                self.current_stimulation_params["sensory_params"][sensory_type]["intensity"] = min(
                    1.0, max(0.0, self.current_stimulation_params["sensory_params"][sensory_type]["intensity"])
                )
    
    def _calculate_session_metrics(self) -> Dict:
        """
        Calculate performance metrics for the session.
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = {}
        
        # Basic metrics
        if self.session_data:
            # Heart rate metrics
            heart_rates = [d.get("heart_rate", 0) for d in self.session_data if "heart_rate" in d]
            if heart_rates:
                metrics["average_heart_rate"] = float(np.mean(heart_rates))
                metrics["max_heart_rate"] = float(np.max(heart_rates))
                metrics["min_heart_rate"] = float(np.min([hr for hr in heart_rates if hr > 0]))
            
            # Power output metrics
            power_values = [d.get("power_output", 0) for d in self.session_data if "power_output" in d]
            if power_values:
                metrics["average_power"] = float(np.mean(power_values))
                metrics["max_power"] = float(np.max(power_values))
            
            # EMG metrics
            emg_values = [d.get("emg_primary", 0) for d in self.session_data if "emg_primary" in d]
            if emg_values:
                metrics["average_muscle_activation"] = float(np.mean(emg_values))
                metrics["peak_muscle_activation"] = float(np.max(emg_values))
        
        # Exercise-specific metrics
        if self._is_rep_based_exercise():
            metrics["total_reps"] = self.rep_count
            
            # Calculate rep rate if we have enough reps
            if self.rep_count > 5:
                session_duration = time.time() - self.session_start_time
                metrics["rep_rate"] = float(self.rep_count / (session_duration / 60))  # reps per minute
        
        # Calculate phase durations
        phase_durations = {phase.name: 0 for phase in ExercisePhase}
        
        last_phase = None
        last_phase_time = self.session_start_time
        
        for data_point in self.session_data:
            current_phase = data_point.get("session_phase")
            current_time = data_point.get("timestamp", last_phase_time)
            
            if current_phase and current_phase != last_phase and last_phase is not None:
                phase_durations[last_phase] += current_time - last_phase_time
                last_phase_time = current_time
            
            last_phase = current_phase
        
        # Add final phase duration
        if last_phase is not None:
            phase_durations[last_phase] += time.time() - last_phase_time
        
        metrics["phase_durations"] = {k: float(v) for k, v in phase_durations.items() if v > 0}
        
        return metrics
    
    def _save_session_data(self, summary: Dict) -> None:
        """
        Save session data to disk.
        
        Args:
            summary: Session summary dictionary
        """
        # Ensure data directory exists
        data_dir = "data/sessions"
        os.makedirs(data_dir, exist_ok=True)
        
        # Save session summary
        summary_path = os.path.join(data_dir, f"{self.session_id}_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed session data
        data_path = os.path.join(data_dir, f"{self.session_id}_data.json")
        with open(data_path, "w") as f:
            json.dump(self.session_data, f, indent=2)
        
        print(f"Session data saved to {data_path} and {summary_path}")


if __name__ == "__main__":
    # Example usage
    controller = SmartOrbStimulationController()
    
    # Set user profile
    user_profile = {
        "name": "John Doe",
        "age": 35,
        "physiological": {
            "max_hr": 185,
            "resting_hr": 65
        },
        "stimulation_response": {
            "tens_sensitivity": 0.9,
            "preferred_frequency": 12
        }
    }
    controller.set_user_profile(user_profile)
    
    # Start session
    session_info = controller.start_session(exercise_type="squat", intensity="moderate")
    print(f"Session started: {session_info}")
    
    # Enable stimulation
    stim_status = controller.toggle_stimulation(True)
    print(f"Stimulation enabled: {stim_status}")
    
    # Simulate processing sensor data
    for i in range(10):
        # Simulate sensor data
        sensor_data = {
            "timestamp": time.time(),
            "heart_rate": 120 + i,
            "emg_primary": 50 + i * 5,
            "accel_x": 0.1,
            "accel_y": 0.2,
            "accel_z": -9.8 if i % 2 == 0 else 5.0  # Simulate repetitive movement
        }
        
        # Process sensor data
        result = controller.process_sensor_data(sensor_data)
        print(f"Processing result: {result}")
        
        # Pause to simulate real-time data
        time.sleep(0.5)
    
    # End session
    summary = controller.end_session()
    print(f"Session ended: {summary}")
