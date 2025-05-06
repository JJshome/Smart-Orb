#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Orb Exercise Enhancement - Synthetic Data Generation

This module generates synthetic data for training and testing the Smart Orb
exercise enhancement models. It simulates various exercise patterns,
physiological responses, and sensor readings that would be captured during
different types of exercise activities.
"""

import numpy as np
import pandas as pd
import random
import json
import os
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


class ExerciseDataGenerator:
    """
    Generates synthetic exercise data for model training and testing.
    """
    
    def __init__(self):
        # Define exercise types
        self.exercise_types = [
            "squat", "deadlift", "bench_press", "shoulder_press",  # Strength
            "running", "cycling", "swimming", "rowing",  # Endurance
            "jumping_jacks", "burpees", "mountain_climbers",  # HIIT
            "yoga", "pilates", "stretching"  # Flexibility
        ]
        
        # Define subject profiles
        self.subject_profiles = self._generate_subject_profiles(100)
        
        # Exercise intensity levels
        self.intensity_levels = ["low", "moderate", "high", "very_high"]
        
        # Sensor configurations
        self.sensor_types = [
            "accelerometer", "gyroscope", "emg", "ecg", "ppg", 
            "gsr", "temperature", "impedance"
        ]
    
    def _generate_subject_profiles(self, num_subjects):
        """
        Generate synthetic subject profiles with various characteristics.
        
        Args:
            num_subjects: Number of synthetic subjects to generate
            
        Returns:
            List of dictionaries containing subject profile information
        """
        profiles = []
        
        for i in range(num_subjects):
            # Generate basic demographic information
            gender = random.choice(["male", "female"])
            
            if gender == "male":
                height = random.normalvariate(175, 10)  # cm
                weight = random.normalvariate(75, 15)   # kg
                body_fat = random.normalvariate(18, 5)  # %
                muscle_mass = random.normalvariate(35, 5)  # %
            else:
                height = random.normalvariate(163, 8)   # cm
                weight = random.normalvariate(65, 12)   # kg
                body_fat = random.normalvariate(25, 6)  # %
                muscle_mass = random.normalvariate(30, 4)  # %
            
            age = random.randint(18, 70)
            
            # Fitness level (1-5 scale)
            fitness_level = max(1, min(5, int(np.random.normal(3, 1))))
            
            # Training experience (years)
            training_experience = max(0, min(30, int(age/3) - random.randint(3, 10)))
            
            # Recovery capacity (1-10 scale, higher is better)
            recovery_capacity = max(1, min(10, int(np.random.normal(7, 2))))
            
            # Generate physiological baseline parameters
            resting_hr = int(random.normalvariate(65, 8))
            # Decrease resting HR based on fitness level
            resting_hr -= (fitness_level - 3) * 3
            resting_hr = max(40, min(90, resting_hr))
            
            max_hr = 220 - age
            hrv_baseline = random.normalvariate(60, 15)
            
            # TENS response parameters
            tens_sensitivity = random.normalvariate(1.0, 0.2)
            tens_effectiveness = random.normalvariate(0.7, 0.15)
            
            profile = {
                "id": f"SUBJ_{i:03d}",
                "age": age,
                "gender": gender,
                "height": round(height, 1),
                "weight": round(weight, 1),
                "bmi": round(weight / ((height/100) ** 2), 1),
                "body_fat": round(body_fat, 1),
                "muscle_mass": round(muscle_mass, 1),
                "fitness_level": fitness_level,
                "training_experience": training_experience,
                "recovery_capacity": recovery_capacity,
                "physiological": {
                    "resting_hr": resting_hr,
                    "max_hr": max_hr,
                    "hrv_baseline": round(hrv_baseline, 1),
                    "vo2max": round(random.normalvariate(35 + (fitness_level * 5), 5), 1),
                    "lactate_threshold": round(random.normalvariate(60 + (fitness_level * 5), 8), 1),
                    "respiratory_rate": round(random.normalvariate(16, 2), 1)
                },
                "stimulation_response": {
                    "tens_sensitivity": round(tens_sensitivity, 2),
                    "tens_effectiveness": round(tens_effectiveness, 2),
                    "preferred_frequency": random.choice([2, 5, 10, 20, 50, 100]),
                    "adaptation_rate": round(random.normalvariate(0.5, 0.15), 2)
                }
            }
            
            profiles.append(profile)
        
        return profiles
    
    def _get_electrode_placement(self, exercise_type):
        """
        Determine appropriate electrode placement based on exercise type.
        
        Args:
            exercise_type: Type of exercise
            
        Returns:
            List of electrode placement locations
        """
        if exercise_type in ["squat", "deadlift"]:
            return ["quadriceps", "hamstrings", "glutes"]
        elif exercise_type in ["bench_press", "shoulder_press"]:
            return ["pectorals", "deltoids", "triceps"]
        elif exercise_type == "running":
            return ["quadriceps", "hamstrings", "calves"]
        elif exercise_type == "cycling":
            return ["quadriceps", "hamstrings", "glutes"]
        elif exercise_type == "swimming":
            return ["deltoids", "lats", "triceps", "trapezius"]
        elif exercise_type == "rowing":
            return ["lats", "rhomboids", "biceps", "quadriceps"]
        elif exercise_type in ["jumping_jacks", "burpees", "mountain_climbers"]:
            return ["quadriceps", "glutes", "deltoids", "core"]
        else:  # Flexibility exercises
            return ["lower_back", "hamstrings", "trapezius"]
    
    def _calculate_performance_metrics(self, data, exercise_type, subject, with_stimulation):
        """
        Calculate performance metrics based on the generated time series data.
        
        Args:
            data: DataFrame with time series data
            exercise_type: Type of exercise
            subject: Subject profile
            with_stimulation: Whether stimulation was active
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = {}
        
        # Common metrics for all exercise types
        metrics["average_heart_rate"] = float(np.mean(data["heart_rate"]))
        metrics["max_heart_rate"] = int(np.max(data["heart_rate"]))
        metrics["average_power"] = float(np.mean(data["power_output"]))
        metrics["max_power"] = float(np.max(data["power_output"]))
        metrics["average_perceived_exertion"] = float(np.mean(data["perceived_exertion"]))
        
        # Calculate heart rate zones (percentage of time in each zone)
        max_hr = subject["physiological"]["max_hr"]
        zone1 = ((data["heart_rate"] >= 0.5*max_hr) & (data["heart_rate"] < 0.6*max_hr)).mean()
        zone2 = ((data["heart_rate"] >= 0.6*max_hr) & (data["heart_rate"] < 0.7*max_hr)).mean()
        zone3 = ((data["heart_rate"] >= 0.7*max_hr) & (data["heart_rate"] < 0.8*max_hr)).mean()
        zone4 = ((data["heart_rate"] >= 0.8*max_hr) & (data["heart_rate"] < 0.9*max_hr)).mean()
        zone5 = (data["heart_rate"] >= 0.9*max_hr).mean()
        
        metrics["hr_zone_distribution"] = {
            "zone1": float(zone1),
            "zone2": float(zone2),
            "zone3": float(zone3),
            "zone4": float(zone4),
            "zone5": float(zone5)
        }
        
        # Calculate muscle activation metrics
        metrics["average_primary_muscle_activation"] = float(np.mean(data["emg_primary"]))
        metrics["average_secondary_muscle_activation"] = float(np.mean(data["emg_secondary"]))
        metrics["peak_primary_muscle_activation"] = float(np.max(data["emg_primary"]))
        
        # Calculate fatigue indicators
        # Simplified - in reality would use more sophisticated algorithms
        late_stage = int(len(data) * 0.7)
        early_stage = int(len(data) * 0.3)
        
        early_power = data["power_output"][early_stage:early_stage+60].mean()  # 1 minute window
        late_power = data["power_output"][late_stage:late_stage+60].mean()   # 1 minute window
        
        if early_power > 0:  # Avoid division by zero
            metrics["power_fatigue_index"] = float(1 - (late_power / early_power))
        else:
            metrics["power_fatigue_index"] = 0.0
        
        # Exercise-specific metrics
        if exercise_type in ["squat", "deadlift", "bench_press", "shoulder_press",
                            "jumping_jacks", "burpees", "mountain_climbers"]:
            # Rep-based exercises
            metrics["total_reps"] = int(data["rep_count"].iloc[-1])
            metrics["average_rep_power"] = float(metrics["average_power"])
            
            # Calculate rep consistency (if enough reps)
            if metrics["total_reps"] > 5:
                rep_intervals = np.diff(np.where(np.diff(data["rep_count"]) > 0)[0])
                if len(rep_intervals) > 1:
                    metrics["rep_consistency"] = float(1 - (np.std(rep_intervals) / np.mean(rep_intervals)))
                else:
                    metrics["rep_consistency"] = 1.0
            else:
                metrics["rep_consistency"] = 1.0
                
        elif exercise_type in ["running", "cycling", "swimming", "rowing"]:
            # Endurance exercises
            metrics["aerobic_efficiency"] = float(metrics["average_power"] / metrics["average_heart_rate"])
            metrics["hr_recovery_rate"] = float(self._calculate_hr_recovery(data["heart_rate"]))
            metrics["steady_state_deviation"] = float(np.std(data["heart_rate"][len(data)//3:len(data)*2//3]))
        
        # If stimulation was used, add stimulation metrics
        if with_stimulation:
            metrics["average_stimulation_intensity"] = float(np.mean(data["stimulation_intensity"]))
            metrics["max_stimulation_intensity"] = float(np.max(data["stimulation_intensity"]))
            
            # Calculate estimated stimulation effectiveness
            # This would normally be based on a more complex analysis
            base_effectiveness = subject["stimulation_response"]["tens_effectiveness"]
            
            # Adjust based on observed metrics
            if "total_reps" in metrics and metrics["total_reps"] > 0:
                # For strength exercises, look at muscle activation vs power
                stim_boost = metrics["average_primary_muscle_activation"] * 1.5 - metrics["power_fatigue_index"]
            else:
                # For endurance, look at heart rate efficiency
                stim_boost = metrics["aerobic_efficiency"] * 0.1
                
            metrics["estimated_stimulation_effectiveness"] = float(base_effectiveness + stim_boost)
            metrics["estimated_performance_boost"] = float(base_effectiveness * 15)  # % improvement
        
        return metrics

    def _calculate_hr_recovery(self, heart_rate_data):
        """
        Calculate heart rate recovery rate from cooldown period.
        
        Args:
            heart_rate_data: Array of heart rate values
        
        Returns:
            Heart rate recovery rate (bpm per minute)
        """
        # Assume cooldown is the last 10% of the session
        cooldown_start = int(len(heart_rate_data) * 0.9)
        cooldown_data = heart_rate_data[cooldown_start:]
        
        if len(cooldown_data) < 60:  # Need at least 60 seconds
            return 0.0
        
        # Calculate rate over first minute of cooldown
        start_hr = cooldown_data[:10].mean()  # Average first 10 seconds
        end_hr = cooldown_data[50:60].mean()  # Average at 1 minute mark
        
        return start_hr - end_hr  # bpm dropped in first minute

    def generate_dataset(self, num_sessions=500, output_dir="/tmp/exercise_data"):
        """
        Generate a complete dataset with multiple exercise sessions and save to disk.
        
        Args:
            num_sessions: Number of exercise sessions to generate
            output_dir: Directory to save the generated data
        
        Returns:
            Dictionary with summary of generated dataset
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save subject profiles
        with open(os.path.join(output_dir, "subjects.json"), "w") as f:
            json.dump(self.subject_profiles, f, indent=2)
        
        # Generate sessions
        sessions_summary = []
        
        for i in range(num_sessions):
            # Randomly select a subject
            subject = random.choice(self.subject_profiles)
            subject_id = subject["id"]
            
            # Randomly determine if stimulation will be used (50% chance)
            with_stimulation = random.choice([True, False])
            
            # Randomly select exercise type and intensity
            exercise_type = random.choice(self.exercise_types)
            intensity = random.choice(self.intensity_levels)
            
            # Generate session
            session = self.generate_exercise_session(
                subject_id, exercise_type, None, intensity, with_stimulation
            )
            
            # Save session metadata and metrics
            session_meta = {
                "session_id": session["session_id"],
                "subject_id": session["subject_id"],
                "exercise_type": session["exercise_type"],
                "intensity": session["intensity"],
                "duration_minutes": session["duration_minutes"],
                "with_stimulation": session["with_stimulation"],
                "performance_metrics": session["performance_metrics"]
            }
            
            sessions_summary.append(session_meta)
            
            # Save session data to CSV
            session_filename = f"session_{session['session_id']}.csv"
            session["time_series_data"].to_csv(
                os.path.join(output_dir, session_filename), index=False
            )
            
            # Save stimulation config if present
            if session["stimulation_config"] is not None:
                stim_filename = f"stim_config_{session['session_id']}.json"
                with open(os.path.join(output_dir, stim_filename), "w") as f:
                    json.dump(session["stimulation_config"], f, indent=2)
            
            # Print progress
            if (i+1) % 50 == 0:
                print(f"Generated {i+1}/{num_sessions} sessions")
        
        # Save sessions summary
        with open(os.path.join(output_dir, "sessions_summary.json"), "w") as f:
            json.dump(sessions_summary, f, indent=2)
        
        return {
            "num_subjects": len(self.subject_profiles),
            "num_sessions": len(sessions_summary),
            "exercise_types": list(set([s["exercise_type"] for s in sessions_summary])),
            "with_stimulation_count": sum(1 for s in sessions_summary if s["with_stimulation"]),
            "without_stimulation_count": sum(1 for s in sessions_summary if not s["with_stimulation"]),
            "output_dir": output_dir
        }


# Example usage
if __name__ == "__main__":
    print("Generating synthetic exercise data...")
    generator = ExerciseDataGenerator()
    
    # Generate a small test dataset
    dataset_info = generator.generate_dataset(num_sessions=10, output_dir="/tmp/exercise_data")
    print(f"Generated dataset: {dataset_info}")
    
    # Generate a single example session
    subject_id = generator.subject_profiles[0]["id"]
    session = generator.generate_exercise_session(
        subject_id, "squat", 20, "high", True
    )
    print(f"Example session: {session['session_id']} for {session['exercise_type']} exercise")
    print(f"Performance metrics: {session['performance_metrics']}")
