#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Orb Web Dashboard

A Flask-based web application that allows users to interact with the Smart Orb
through a web interface, visualize data, and test different stimulation modes
using simulated data.
"""

import os
import sys
import json
import time
import uuid
import threading
import numpy as np
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
import plotly
import plotly.graph_objs as go

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exercise_enhancement.stimulation_controller import SmartOrbStimulationController, ExercisePhase, ExerciseType

# Initialize Flask app
app = Flask(__name__)

# Global session store
active_sessions = {}

# User profiles
user_profiles = {
    "default": {
        "name": "Default User",
        "age": 30,
        "physiological": {
            "max_hr": 190,
            "resting_hr": 60
        },
        "stimulation_response": {
            "tens_sensitivity": 0.85,
            "preferred_frequency": 10
        }
    },
    "athlete": {
        "name": "Athletic User",
        "age": 25,
        "physiological": {
            "max_hr": 195,
            "resting_hr": 50
        },
        "stimulation_response": {
            "tens_sensitivity": 0.9,
            "preferred_frequency": 12
        }
    },
    "senior": {
        "name": "Senior User",
        "age": 65,
        "physiological": {
            "max_hr": 155,
            "resting_hr": 70
        },
        "stimulation_response": {
            "tens_sensitivity": 0.7,
            "preferred_frequency": 8
        }
    }
}

def create_simulation_thread(session_id, exercise_type, intensity, duration):
    """
    Create a thread to run the simulation.
    
    Args:
        session_id: Unique session identifier
        exercise_type: Type of exercise to simulate
        intensity: Exercise intensity level
        duration: Simulation duration in seconds
    """
    def simulation_worker(session_id, exercise_type, intensity, duration):
        session = active_sessions[session_id]
        controller = session["controller"]
        
        # Start session
        controller.start_session(exercise_type=exercise_type, intensity=intensity)
        
        # Enable stimulation
        controller.toggle_stimulation(True)
        
        # Simulation parameters
        start_time = time.time()
        elapsed_time = 0
        
        # Store data for charting
        session["data"] = {
            "timestamps": [],
            "heart_rate": [],
            "emg": [],
            "accel_z": [],
            "tens_intensity": [],
            "tens_frequency": [],
            "phase": []
        }
        
        # Duration for each phase (simplified)
        phase_durations = {
            ExercisePhase.SETUP: duration * 0.05,    # 5% of time
            ExercisePhase.WARMUP: duration * 0.15,   # 15% of time
            ExercisePhase.MAIN: duration * 0.6,      # 60% of time
            ExercisePhase.COOLDOWN: duration * 0.15, # 15% of time
            ExercisePhase.RECOVERY: duration * 0.05  # 5% of time
        }
        
        # Determine category
        exercise_category = controller._get_exercise_category(exercise_type)
        
        # Intensity factors for heart rate
        hr_factors = {
            "low": 0.6,
            "moderate": 0.7,
            "high": 0.8,
            "very_high": 0.9
        }
        hr_factor = hr_factors.get(intensity, 0.7)
        user_profile = session["user_profile"]
        max_hr = user_profile["physiological"]["max_hr"]
        resting_hr = user_profile["physiological"]["resting_hr"]
        
        try:
            # Simulation loop
            while elapsed_time < duration and not session.get("stopped", False):
                elapsed_time = time.time() - start_time
                
                # Real time scaling factor (speed up simulation by 10x)
                sim_time = elapsed_time * 10
                
                # Determine current phase based on sim_time
                current_phase = ExercisePhase.SETUP
                phase_end_time = phase_durations[ExercisePhase.SETUP]
                
                if sim_time > phase_end_time:
                    current_phase = ExercisePhase.WARMUP
                    phase_end_time += phase_durations[ExercisePhase.WARMUP]
                    
                    if sim_time > phase_end_time:
                        current_phase = ExercisePhase.MAIN
                        phase_end_time += phase_durations[ExercisePhase.MAIN]
                        
                        if sim_time > phase_end_time:
                            current_phase = ExercisePhase.COOLDOWN
                            phase_end_time += phase_durations[ExercisePhase.COOLDOWN]
                            
                            if sim_time > phase_end_time:
                                current_phase = ExercisePhase.RECOVERY
                
                # Generate simulated sensor data
                heart_rate = simulate_heart_rate(
                    current_phase, 
                    sim_time, 
                    duration,
                    resting_hr,
                    max_hr,
                    hr_factor
                )
                
                accel_x, accel_y, accel_z = simulate_acceleration(
                    exercise_category,
                    exercise_type,
                    current_phase,
                    sim_time,
                    int(sim_time)  # Counter
                )
                
                emg = simulate_emg(
                    exercise_category,
                    current_phase,
                    sim_time,
                    int(sim_time)
                )
                
                # Create sensor data point
                sensor_data = {
                    "timestamp": time.time(),
                    "heart_rate": heart_rate,
                    "accel_x": accel_x,
                    "accel_y": accel_y,
                    "accel_z": accel_z,
                    "emg_primary": emg,
                    "power_output": heart_rate * 0.5 * (1 + np.sin(sim_time / 10)) if exercise_category == ExerciseType.ENDURANCE else None,
                    "exercise_phase": current_phase.name
                }
                
                # Process with controller
                result = controller.process_sensor_data(sensor_data)
                
                # Extract TENS parameters if available
                tens_intensity = 0
                tens_frequency = 0
                
                if "stimulation" in result and result["stimulation"] is not None:
                    stim = result["stimulation"]
                    tens_intensity = stim["tens_params"].get("intensity", 0)
                    tens_frequency = stim["tens_params"].get("frequency", 0)
                
                # Store data for charting
                session["data"]["timestamps"].append(elapsed_time)
                session["data"]["heart_rate"].append(heart_rate)
                session["data"]["emg"].append(emg)
                session["data"]["accel_z"].append(accel_z)
                session["data"]["tens_intensity"].append(tens_intensity)
                session["data"]["tens_frequency"].append(tens_frequency)
                session["data"]["phase"].append(current_phase.name)
                
                # Update session status
                session["status"] = {
                    "elapsed_time": elapsed_time,
                    "total_duration": duration,
                    "current_phase": current_phase.name,
                    "heart_rate": heart_rate,
                    "emg": emg,
                    "tens_intensity": tens_intensity,
                    "tens_frequency": tens_frequency
                }
                
                # Wait to control simulation speed
                time.sleep(0.1)  # Update every 100ms (10 updates per second)
            
            # End session if not stopped manually
            if not session.get("stopped", False):
                summary = controller.end_session()
                session["summary"] = summary
                session["status"]["completed"] = True
        
        except Exception as e:
            session["error"] = str(e)
            print(f"Simulation error: {e}")
        
        finally:
            # Mark simulation as complete
            session["status"]["running"] = False
    
    # Create and start the thread
    thread = threading.Thread(
        target=simulation_worker,
        args=(session_id, exercise_type, intensity, duration)
    )
    thread.daemon = True
    thread.start()
    
    return thread

def simulate_heart_rate(phase, elapsed_time, total_duration, resting_hr, max_hr, intensity_factor):
    """
    Simulate heart rate based on exercise phase and intensity.
    
    Args:
        phase: Current exercise phase
        elapsed_time: Elapsed time in seconds
        total_duration: Total session duration in seconds
        resting_hr: Resting heart rate
        max_hr: Maximum heart rate
        intensity_factor: Intensity factor (0-1)
        
    Returns:
        Simulated heart rate
    """
    target_hr = resting_hr  # Default for SETUP and RECOVERY
    
    if phase == ExercisePhase.WARMUP:
        # Linear increase during warmup
        phase_progress = elapsed_time / (total_duration * 0.15)  # Warmup is 15% of total
        target_hr = resting_hr + (max_hr * intensity_factor - resting_hr) * min(1.0, phase_progress)
    
    elif phase == ExercisePhase.MAIN:
        # Fluctuating around target during main phase
        main_start = total_duration * 0.2  # After SETUP and WARMUP
        time_in_main = elapsed_time - main_start
        target_hr = max_hr * intensity_factor
        fluctuation = np.sin(time_in_main / 30) * 5  # ±5 BPM fluctuation
        target_hr += fluctuation
    
    elif phase == ExercisePhase.COOLDOWN:
        # Exponential decrease during cooldown
        cooldown_start = total_duration * 0.8  # Start of cooldown
        time_in_cooldown = elapsed_time - cooldown_start
        cooldown_duration = total_duration * 0.15  # Cooldown is 15% of total
        decay_factor = np.exp(-3 * time_in_cooldown / cooldown_duration)
        target_hr = resting_hr + (max_hr * intensity_factor - resting_hr) * decay_factor
    
    # Add some noise
    noise = np.random.normal(0, 2)  # ±2 BPM gaussian noise
    heart_rate = target_hr + noise
    
    return max(resting_hr - 5, min(max_hr + 5, heart_rate))  # Clamp within reasonable range

def simulate_acceleration(exercise_category, exercise_type, phase, elapsed_time, counter):
    """
    Simulate accelerometer data based on exercise type and phase.
    
    Args:
        exercise_category: Type of exercise
        exercise_type: Specific exercise name
        phase: Current exercise phase
        elapsed_time: Elapsed time in seconds
        counter: Counter for periodic movements
        
    Returns:
        Tuple of (accel_x, accel_y, accel_z)
    """
    # Default values (gravity)
    accel_x, accel_y, accel_z = 0.0, 0.0, -9.8
    
    # No significant movement during SETUP or RECOVERY
    if phase == ExercisePhase.SETUP or phase == ExercisePhase.RECOVERY:
        # Just add a little noise
        noise_x = np.random.normal(0, 0.1)
        noise_y = np.random.normal(0, 0.1)
        noise_z = np.random.normal(0, 0.1)
        return accel_x + noise_x, accel_y + noise_y, accel_z + noise_z
    
    # Different patterns based on exercise category
    if exercise_category == ExerciseType.STRENGTH:
        # Strength exercises have distinct repetitive movements
        if exercise_type == "squat":
            # Squats have strong vertical (z) movement
            if phase == ExercisePhase.MAIN:
                # One repetition takes about 4 seconds
                rep_phase = (counter % 4) / 4.0
                
                if rep_phase < 0.4:  # Going down
                    accel_z = -9.8 - 5.0 * rep_phase / 0.4  # Acceleration increases
                elif rep_phase < 0.5:  # Bottom position
                    accel_z = -14.8
                elif rep_phase < 0.9:  # Going up
                    accel_z = -14.8 + 10.0 * (rep_phase - 0.5) / 0.4  # Deceleration
                else:  # Top position
                    accel_z = -4.8
            else:  # WARMUP or COOLDOWN
                # Less intense movements
                rep_phase = (counter % 6) / 6.0  # Slower reps
                if rep_phase < 0.5:
                    accel_z = -9.8 - 3.0 * np.sin(rep_phase * np.pi)
                else:
                    accel_z = -9.8 - 3.0 * np.sin(rep_phase * np.pi)
        
        elif exercise_type == "deadlift":
            # Deadlifts have strong vertical (z) movement but different pattern
            if phase == ExercisePhase.MAIN:
                # One repetition takes about 5 seconds
                rep_phase = (counter % 5) / 5.0
                
                if rep_phase < 0.3:  # Initial pull
                    accel_z = -9.8 + 8.0 * rep_phase / 0.3
                elif rep_phase < 0.5:  # Lockout
                    accel_z = -1.8
                elif rep_phase < 0.8:  # Lowering
                    accel_z = -1.8 - 8.0 * (rep_phase - 0.5) / 0.3
                else:  # Reset
                    accel_z = -9.8
            else:  # WARMUP or COOLDOWN
                # Less intense movements
                rep_phase = (counter % 8) / 8.0  # Slower reps
                accel_z = -9.8 + 5.0 * np.sin(rep_phase * np.pi)
    
    elif exercise_category == ExerciseType.ENDURANCE:
        # Endurance exercises have rhythmic movements
        if exercise_type == "running":
            # Running has vertical bouncing and forward acceleration
            step_frequency = 3.0  # steps per second (for both feet combined)
            
            if phase == ExercisePhase.MAIN:
                # Forward motion (x-axis)
                accel_x = 2.0 + 1.0 * np.sin(counter * step_frequency * np.pi)
                # Lateral movement (y-axis)
                accel_y = 0.5 * np.sin(counter * step_frequency * np.pi / 2)
                # Vertical bounce (z-axis)
                accel_z = -9.8 + 6.0 * abs(np.sin(counter * step_frequency * np.pi))
            else:  # WARMUP or COOLDOWN
                # Slower, less intense
                slower_freq = 2.0
                accel_x = 1.0 + 0.5 * np.sin(counter * slower_freq * np.pi)
                accel_y = 0.3 * np.sin(counter * slower_freq * np.pi / 2)
                accel_z = -9.8 + 3.0 * abs(np.sin(counter * slower_freq * np.pi))
        
        elif exercise_type == "cycling":
            # Cycling has smoother patterns
            pedal_frequency = 1.5  # Complete cycles per second
            
            if phase == ExercisePhase.MAIN:
                # Mostly forward motion (x-axis)
                accel_x = 1.5 + 0.3 * np.sin(counter * pedal_frequency * np.pi * 2)
                # Some lateral movement (y-axis) from rocking
                accel_y = 0.2 * np.sin(counter * pedal_frequency * np.pi)
                # Minimal vertical (z-axis) changes
                accel_z = -9.8 + 0.5 * np.sin(counter * pedal_frequency * np.pi * 2)
            else:  # WARMUP or COOLDOWN
                slower_freq = 1.0
                accel_x = 0.8 + 0.2 * np.sin(counter * slower_freq * np.pi * 2)
                accel_y = 0.1 * np.sin(counter * slower_freq * np.pi)
                accel_z = -9.8 + 0.3 * np.sin(counter * slower_freq * np.pi * 2)
    
    elif exercise_category == ExerciseType.HIIT:
        # HIIT has alternating intense and rest periods
        cycle_duration = 60  # seconds (e.g., 30s work, 30s rest)
        cycle_phase = (elapsed_time % cycle_duration) / cycle_duration
        is_work_phase = cycle_phase < 0.5  # First half is work, second half is rest
        
        if exercise_type == "burpees":
            if phase == ExercisePhase.MAIN and is_work_phase:
                # Burpees have complex movement patterns
                rep_duration = 3  # seconds per rep
                rep_phase = (counter % rep_duration) / rep_duration
                
                if rep_phase < 0.2:  # Squat down
                    accel_z = -9.8 - 5.0 * rep_phase / 0.2
                    accel_x = 0.5 * rep_phase / 0.2
                elif rep_phase < 0.4:  # Kick out
                    accel_z = -14.8
                    accel_x = 0.5 + 3.0 * (rep_phase - 0.2) / 0.2
                elif rep_phase < 0.6:  # Push-up position
                    accel_z = -14.8 + 2.0 * (rep_phase - 0.4) / 0.2
                    accel_x = 3.5 - 1.0 * (rep_phase - 0.4) / 0.2
                elif rep_phase < 0.8:  # Jump in
                    accel_z = -12.8 - 2.0 * (rep_phase - 0.6) / 0.2
                    accel_x = 2.5 - 2.5 * (rep_phase - 0.6) / 0.2
                else:  # Jump up
                    accel_z = -14.8 + 20.0 * (rep_phase - 0.8) / 0.2
                    accel_x = 0
            else:  # WARMUP, COOLDOWN, or REST phase
                # Less intense, some random movement
                accel_x = 0.5 * np.random.normal(0, 1)
                accel_y = 0.5 * np.random.normal(0, 1)
                accel_z = -9.8 + 0.5 * np.random.normal(0, 1)
    
    # Add some random noise to all readings
    noise_x = np.random.normal(0, 0.2)
    noise_y = np.random.normal(0, 0.2)
    noise_z = np.random.normal(0, 0.2)
    
    return accel_x + noise_x, accel_y + noise_y, accel_z + noise_z

def simulate_emg(exercise_category, phase, elapsed_time, counter):
    """
    Simulate EMG data based on exercise type and phase.
    
    Args:
        exercise_category: Type of exercise
        phase: Current exercise phase
        elapsed_time: Elapsed time in seconds
        counter: Counter for periodic movements
        
    Returns:
        Simulated EMG value
    """
    # Base EMG level based on phase
    if phase == ExercisePhase.SETUP:
        base_emg = 5.0  # Very low muscle activity
    elif phase == ExercisePhase.WARMUP:
        base_emg = 20.0  # Some muscle activity
    elif phase == ExercisePhase.MAIN:
        base_emg = 50.0  # High muscle activity
    elif phase == ExercisePhase.COOLDOWN:
        base_emg = 15.0  # Reduced muscle activity
    else:  # RECOVERY
        base_emg = 5.0  # Very low muscle activity
    
    # Adjust based on exercise category
    if exercise_category == ExerciseType.STRENGTH:
        # Strong peaks during contractions
        if phase == ExercisePhase.MAIN:
            rep_duration = 4  # seconds per rep
            rep_phase = (counter % rep_duration) / rep_duration
            
            if rep_phase < 0.4:  # Eccentric phase
                emg_factor = 1.0 + rep_phase * 1.5  # Gradual increase
            elif rep_phase < 0.6:  # Isometric hold
                emg_factor = 2.0  # Maximum contraction
            elif rep_phase < 0.9:  # Concentric phase
                emg_factor = 2.0 - (rep_phase - 0.6) * 1.5  # Gradual decrease
            else:  # Rest at top
                emg_factor = 0.5
        else:
            # Less intense patterns for warmup/cooldown
            emg_factor = 0.7 + 0.3 * np.sin(counter / 2)
    
    elif exercise_category == ExerciseType.ENDURANCE:
        # Rhythmic, moderate activity
        cycle_freq = 1.0  # cycles per second
        emg_factor = 0.8 + 0.4 * abs(np.sin(counter * cycle_freq * np.pi))
    
    elif exercise_category == ExerciseType.HIIT:
        # Alternating high/low activity
        cycle_duration = 60  # seconds (e.g., 30s work, 30s rest)
        cycle_phase = (elapsed_time % cycle_duration) / cycle_duration
        
        if cycle_phase < 0.5:  # Work phase
            # High intensity with some bursts
            emg_factor = 1.5 + 0.5 * np.sin(counter / 1.5)
        else:  # Rest phase
            # Lower intensity
            emg_factor = 0.4 + 0.1 * np.sin(counter / 2)
    
    elif exercise_category == ExerciseType.FLEXIBILITY:
        # Lower but sustained activity
        emg_factor = 0.6 + 0.2 * np.sin(counter / 10)
    
    else:  # Unknown exercise type
        emg_factor = 1.0
    
    # Calculate final EMG value
    emg = base_emg * emg_factor
    
    # Add some noise
    noise = np.random.normal(0, emg * 0.05)  # 5% noise
    
    return max(1.0, emg + noise)  # Ensure positive value

def create_charts(session_id):
    """
    Create charts for the given session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Dictionary of chart JSON data
    """
    session = active_sessions[session_id]
    data = session["data"]
    
    if not data["timestamps"]:
        return {}
    
    # Heart Rate Chart
    heart_rate_trace = go.Scatter(
        x=data["timestamps"],
        y=data["heart_rate"],
        mode='lines',
        name='Heart Rate',
        line=dict(color='rgb(219, 64, 82)', width=2)
    )
    
    heart_rate_layout = go.Layout(
        title='Heart Rate',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='BPM'),
        margin=dict(l=50, r=50, b=50, t=50),
        height=300
    )
    
    heart_rate_chart = json.dumps(dict(data=[heart_rate_trace], layout=heart_rate_layout), cls=plotly.utils.PlotlyJSONEncoder)
    
    # EMG Chart
    emg_trace = go.Scatter(
        x=data["timestamps"],
        y=data["emg"],
        mode='lines',
        name='EMG',
        line=dict(color='rgb(50, 168, 82)', width=2)
    )
    
    emg_layout = go.Layout(
        title='Muscle Activity (EMG)',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='EMG Units'),
        margin=dict(l=50, r=50, b=50, t=50),
        height=300
    )
    
    emg_chart = json.dumps(dict(data=[emg_trace], layout=emg_layout), cls=plotly.utils.PlotlyJSONEncoder)
    
    # Acceleration Chart
    accel_trace = go.Scatter(
        x=data["timestamps"],
        y=data["accel_z"],
        mode='lines',
        name='Z-Acceleration',
        line=dict(color='rgb(66, 134, 244)', width=2)
    )
    
    accel_layout = go.Layout(
        title='Vertical Acceleration',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='m/s²'),
        margin=dict(l=50, r=50, b=50, t=50),
        height=300
    )
    
    accel_chart = json.dumps(dict(data=[accel_trace], layout=accel_layout), cls=plotly.utils.PlotlyJSONEncoder)
    
    # TENS Stimulation Chart
    tens_intensity_trace = go.Scatter(
        x=data["timestamps"],
        y=data["tens_intensity"],
        mode='lines',
        name='Intensity (mA)',
        line=dict(color='rgb(255, 99, 132)', width=2)
    )
    
    tens_frequency_trace = go.Scatter(
        x=data["timestamps"],
        y=data["tens_frequency"],
        mode='lines',
        name='Frequency (Hz)',
        line=dict(color='rgb(54, 162, 235)', width=2, dash='dash')
    )
    
    tens_layout = go.Layout(
        title='TENS Stimulation Parameters',
        xaxis=dict(title='Time (s)'),
        yaxis=dict(title='Value'),
        margin=dict(l=50, r=50, b=50, t=50),
        height=300,
        legend=dict(orientation='h', y=1.1)
    )
    
    tens_chart = json.dumps(dict(data=[tens_intensity_trace, tens_frequency_trace], layout=tens_layout), cls=plotly.utils.PlotlyJSONEncoder)
    
    # Exercise Phases
    unique_phases = []
    phase_start_times = []
    
    current_phase = None
    for i, phase in enumerate(data["phase"]):
        if phase != current_phase:
            current_phase = phase
            if i > 0:  # Skip the first point
                unique_phases.append(phase)
                phase_start_times.append(data["timestamps"][i])
    
    # Return all charts
    return {
        "heart_rate_chart": heart_rate_chart,
        "emg_chart": emg_chart,
        "accel_chart": accel_chart,
        "tens_chart": tens_chart,
        "phases": {
            "names": unique_phases,
            "times": phase_start_times
        }
    }

@app.route('/')
def index():
    """Render the main dashboard page."""
    exercise_types = [
        {"id": "squat", "name": "Squat", "category": "STRENGTH"},
        {"id": "deadlift", "name": "Deadlift", "category": "STRENGTH"},
        {"id": "bench_press", "name": "Bench Press", "category": "STRENGTH"},
        {"id": "running", "name": "Running", "category": "ENDURANCE"},
        {"id": "cycling", "name": "Cycling", "category": "ENDURANCE"},
        {"id": "burpees", "name": "Burpees", "category": "HIIT"},
        {"id": "jumping_jacks", "name": "Jumping Jacks", "category": "HIIT"},
        {"id": "yoga", "name": "Yoga", "category": "FLEXIBILITY"}
    ]
    
    intensities = [
        {"id": "low", "name": "Low"},
        {"id": "moderate", "name": "Moderate"},
        {"id": "high", "name": "High"},
        {"id": "very_high", "name": "Very High"}
    ]
    
    # Available user profiles
    profiles = []
    for profile_id, profile in user_profiles.items():
        profiles.append({
            "id": profile_id,
            "name": profile["name"],
            "age": profile["age"]
        })
    
    return render_template('index.html', 
                          exercise_types=exercise_types, 
                          intensities=intensities,
                          profiles=profiles)

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    """Start a new simulation session."""
    # Get parameters from form
    data = request.get_json()
    exercise_type = data.get('exercise_type', 'squat')
    intensity = data.get('intensity', 'moderate')
    duration = int(data.get('duration', 60))
    profile_id = data.get('profile', 'default')
    
    # Create a new session
    session_id = str(uuid.uuid4())
    
    # Get user profile
    user_profile = user_profiles.get(profile_id, user_profiles['default'])
    
    # Initialize controller
    controller = SmartOrbStimulationController()
    controller.set_user_profile(user_profile)
    
    # Create session
    active_sessions[session_id] = {
        "controller": controller,
        "exercise_type": exercise_type,
        "intensity": intensity,
        "duration": duration,
        "user_profile": user_profile,
        "start_time": time.time(),
        "status": {
            "running": True,
            "completed": False,
            "elapsed_time": 0,
            "total_duration": duration,
            "current_phase": "SETUP"
        }
    }
    
    # Start simulation thread
    create_simulation_thread(session_id, exercise_type, intensity, duration)
    
    return jsonify({
        "session_id": session_id,
        "message": f"Started simulation for {exercise_type} ({intensity} intensity)"
    })

@app.route('/stop_simulation/<session_id>', methods=['POST'])
def stop_simulation(session_id):
    """Stop a running simulation."""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        session["stopped"] = True
        
        # End the session in the controller
        controller = session["controller"]
        try:
            summary = controller.end_session()
            session["summary"] = summary
        except Exception as e:
            session["error"] = str(e)
        
        session["status"]["running"] = False
        
        return jsonify({
            "message": "Simulation stopped",
            "session_id": session_id
        })
    
    return jsonify({
        "error": "Session not found"
    }), 404

@app.route('/session_status/<session_id>')
def session_status(session_id):
    """Get the status of a simulation session."""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        
        # Create charts if there's data
        charts = {}
        if "data" in session and session["data"].get("timestamps", []):
            charts = create_charts(session_id)
        
        return jsonify({
            "session_id": session_id,
            "status": session["status"],
            "charts": charts,
            "summary": session.get("summary", {}),
            "error": session.get("error", None)
        })
    
    return jsonify({
        "error": "Session not found"
    }), 404

@app.route('/active_sessions')
def get_active_sessions():
    """Get all active simulation sessions."""
    sessions = {}
    for session_id, session in active_sessions.items():
        sessions[session_id] = {
            "exercise_type": session["exercise_type"],
            "intensity": session["intensity"],
            "start_time": session.get("start_time", 0),
            "status": session["status"]
        }
    
    return jsonify(sessions)

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Create static and templates directories if they don't exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Start server
    app.run(debug=True, host='0.0.0.0', port=5000)
