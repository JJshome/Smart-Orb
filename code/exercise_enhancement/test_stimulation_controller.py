#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the Smart Orb Exercise Enhancement Stimulation Controller.
This script demonstrates the usage of the stimulation controller with simulated sensor data.
"""

import time
import json
import numpy as np
import matplotlib.pyplot as plt
import os
from typing import Dict, List, Tuple
from stimulation_controller import SmartOrbStimulationController, ExercisePhase, ExerciseType


def simulate_exercise_session(exercise_type: str, duration_seconds: int, 
                             intensity: str, plot_results: bool = True) -> Tuple[Dict, List[Dict]]:
    """
    Simulate an exercise session with the Smart Orb stimulation controller.
    
    Args:
        exercise_type: Type of exercise to simulate (e.g., "squat", "running")
        duration_seconds: Duration of the simulated session in seconds
        intensity: Exercise intensity ("low", "moderate", "high", "very_high")
        plot_results: Whether to plot the simulation results
        
    Returns:
        Tuple of (session summary, sensor data history)
    """
    # Initialize controller
    controller = SmartOrbStimulationController()
    
    # Set user profile
    user_profile = {
        "name": "Test User",
        "age": 30,
        "physiological": {
            "max_hr": 190,
            "resting_hr": 60
        },
        "stimulation_response": {
            "tens_sensitivity": 0.85,
            "preferred_frequency": 10
        }
    }
    controller.set_user_profile(user_profile)
    
    # Start session
    print(f"Starting {intensity} intensity {exercise_type} session...")
    session_info = controller.start_session(exercise_type=exercise_type, intensity=intensity)
    print(f"Session started: {session_info}")
    
    # Enable stimulation
    stim_status = controller.toggle_stimulation(True)
    print(f"Stimulation enabled: {stim_status}")
    
    # Prepare for data collection
    start_time = time.time()
    sensor_data_history = []
    processing_results = []
    
    # Duration for each phase (simplified)
    phase_durations = {
        ExercisePhase.SETUP: duration_seconds * 0.05,    # 5% of time
        ExercisePhase.WARMUP: duration_seconds * 0.15,   # 15% of time
        ExercisePhase.MAIN: duration_seconds * 0.6,      # 60% of time
        ExercisePhase.COOLDOWN: duration_seconds * 0.15, # 15% of time
        ExercisePhase.RECOVERY: duration_seconds * 0.05  # 5% of time
    }
    
    # Generate simulated data based on exercise type and intensity
    exercise_category = controller._get_exercise_category(exercise_type)
    
    # Intensity factors for heart rate
    hr_factors = {
        "low": 0.6,
        "moderate": 0.7,
        "high": 0.8,
        "very_high": 0.9
    }
    hr_factor = hr_factors.get(intensity, 0.7)
    max_hr = user_profile["physiological"]["max_hr"]
    resting_hr = user_profile["physiological"]["resting_hr"]
    
    # Simulate data points (1 per second)
    for i in range(duration_seconds):
        current_time = start_time + i
        elapsed_time = i
        
        # Determine current phase based on elapsed time
        current_phase = ExercisePhase.SETUP
        phase_end_time = phase_durations[ExercisePhase.SETUP]
        
        if elapsed_time > phase_end_time:
            current_phase = ExercisePhase.WARMUP
            phase_end_time += phase_durations[ExercisePhase.WARMUP]
            
            if elapsed_time > phase_end_time:
                current_phase = ExercisePhase.MAIN
                phase_end_time += phase_durations[ExercisePhase.MAIN]
                
                if elapsed_time > phase_end_time:
                    current_phase = ExercisePhase.COOLDOWN
                    phase_end_time += phase_durations[ExercisePhase.COOLDOWN]
                    
                    if elapsed_time > phase_end_time:
                        current_phase = ExercisePhase.RECOVERY
        
        # Generate heart rate based on phase and intensity
        heart_rate = simulate_heart_rate(
            current_phase, 
            elapsed_time, 
            duration_seconds,
            resting_hr,
            max_hr,
            hr_factor
        )
        
        # Generate accelerometer data based on exercise type and phase
        accel_x, accel_y, accel_z = simulate_acceleration(
            exercise_category,
            exercise_type,
            current_phase,
            elapsed_time,
            i  # Use as a counter for periodic movements
        )
        
        # Generate EMG data
        emg_primary = simulate_emg(
            exercise_category,
            current_phase,
            elapsed_time,
            i
        )
        
        # Create sensor data point
        sensor_data = {
            "timestamp": current_time,
            "heart_rate": heart_rate,
            "accel_x": accel_x,
            "accel_y": accel_y,
            "accel_z": accel_z,
            "emg_primary": emg_primary,
            "power_output": heart_rate * 0.5 * (1 + np.sin(i / 10)) if exercise_category == ExerciseType.ENDURANCE else None,
            "exercise_phase": current_phase.name
        }
        
        # Process with controller
        processing_result = controller.process_sensor_data(sensor_data)
        
        # Store for later analysis
        sensor_data_history.append(sensor_data)
        processing_results.append(processing_result)
        
        # Print status every 10 seconds
        if i % 10 == 0:
            print(f"  Time: {i}s, Phase: {current_phase.name}, HR: {heart_rate}, EMG: {emg_primary:.1f}")
            if "stimulation" in processing_result:
                stim_params = processing_result["stimulation"]["tens_params"]
                print(f"  TENS: {stim_params['intensity']:.1f}mA, {stim_params['frequency']}Hz")
    
    # End session
    summary = controller.end_session()
    print(f"Session ended: {summary}")
    
    # Plot results if requested
    if plot_results:
        plot_session_data(sensor_data_history, processing_results, exercise_type, intensity)
    
    return summary, sensor_data_history


def simulate_heart_rate(
    phase: ExercisePhase,
    elapsed_time: int,
    total_duration: int,
    resting_hr: int,
    max_hr: int,
    intensity_factor: float
) -> float:
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


def simulate_acceleration(
    exercise_category: ExerciseType,
    exercise_type: str,
    phase: ExercisePhase,
    elapsed_time: int,
    counter: int
) -> Tuple[float, float, float]:
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
    
    elif exercise_category == ExerciseType.FLEXIBILITY:
        # Flexibility exercises have slow, controlled movements
        if exercise_type == "yoga":
            # Yoga poses change slowly with hold periods
            pose_duration = 20  # seconds per pose
            transition_duration = 5  # seconds to transition
            
            cycle_time = elapsed_time % (pose_duration + transition_duration)
            in_transition = cycle_time < transition_duration
            
            if in_transition:
                # Smooth transition between poses
                transition_factor = cycle_time / transition_duration
                accel_x = 0.5 * np.sin(transition_factor * np.pi)
                accel_y = 0.5 * np.cos(transition_factor * np.pi)
                accel_z = -9.8 + 1.0 * np.sin(transition_factor * np.pi * 2)
            else:
                # Small adjustments during pose holds
                accel_x = 0.2 * np.sin(counter / 10)
                accel_y = 0.2 * np.cos(counter / 10)
                accel_z = -9.8 + 0.3 * np.sin(counter / 5)
    
    # Add some random noise to all readings
    noise_x = np.random.normal(0, 0.2)
    noise_y = np.random.normal(0, 0.2)
    noise_z = np.random.normal(0, 0.2)
    
    return accel_x + noise_x, accel_y + noise_y, accel_z + noise_z


def simulate_emg(
    exercise_category: ExerciseType,
    phase: ExercisePhase,
    elapsed_time: int,
    counter: int
) -> float:
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


def plot_session_data(sensor_data_history: List[Dict], processing_results: List[Dict], 
                     exercise_type: str, intensity: str) -> None:
    """
    Plot the session data for visualization.
    
    Args:
        sensor_data_history: List of sensor data points
        processing_results: List of processing results from controller
        exercise_type: Exercise type name
        intensity: Exercise intensity
    """
    timestamps = [d["timestamp"] for d in sensor_data_history]
    start_time = timestamps[0]
    times = [(t - start_time) for t in timestamps]  # Convert to elapsed seconds
    
    # Extract sensor data
    heart_rates = [d.get("heart_rate", 0) for d in sensor_data_history]
    accel_z = [d.get("accel_z", 0) for d in sensor_data_history]
    emg = [d.get("emg_primary", 0) for d in sensor_data_history]
    
    # Extract stimulation parameters if available
    tens_intensity = []
    tens_frequency = []
    
    for result in processing_results:
        if "stimulation" in result and result["stimulation"] is not None:
            stim = result["stimulation"]
            tens_intensity.append(stim["tens_params"].get("intensity", 0))
            tens_frequency.append(stim["tens_params"].get("frequency", 0))
        else:
            tens_intensity.append(0)
            tens_frequency.append(0)
    
    # Plot
    fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"{exercise_type.capitalize()} Exercise - {intensity.capitalize()} Intensity", fontsize=16)
    
    # Heart rate
    axs[0].plot(times, heart_rates, 'r-')
    axs[0].set_ylabel('Heart Rate (BPM)')
    axs[0].grid(True)
    
    # Acceleration
    axs[1].plot(times, accel_z, 'g-')
    axs[1].set_ylabel('Z-Acceleration (m/s²)')
    axs[1].grid(True)
    
    # EMG
    axs[2].plot(times, emg, 'b-')
    axs[2].set_ylabel('EMG Activity')
    axs[2].grid(True)
    
    # TENS stimulation
    axs[3].plot(times, tens_intensity, 'r-', label='Intensity (mA)')
    axs[3].plot(times, tens_frequency, 'b--', label='Frequency (Hz)')
    axs[3].set_xlabel('Time (seconds)')
    axs[3].set_ylabel('TENS Parameters')
    axs[3].legend()
    axs[3].grid(True)
    
    # Add exercise phases
    phases = [result.get("session_phase", "") for result in processing_results]
    phase_starts = []
    phase_labels = []
    
    current_phase = None
    for i, phase in enumerate(phases):
        if phase != current_phase:
            current_phase = phase
            phase_starts.append(times[i])
            phase_labels.append(phase)
    
    # Draw vertical lines for phase transitions
    for ax in axs:
        for i, phase_time in enumerate(phase_starts[1:], 1):  # Skip first phase start (0)
            ax.axvline(x=phase_time, color='k', linestyle='--', alpha=0.5)
            if ax == axs[0]:  # Only add text in the first subplot
                ax.text(phase_time, ax.get_ylim()[1] * 0.9, phase_labels[i], 
                       rotation=90, verticalalignment='top')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Save plot
    filename = f"output/{exercise_type}_{intensity}_simulation.png"
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.close()


if __name__ == "__main__":
    # Example simulations
    print("\n=== Running exercise simulations ===")
    
    # Simulate a strength exercise session
    print("\n1. Strength exercise simulation")
    simulate_exercise_session("squat", 120, "high", True)
    
    # Simulate an endurance exercise session
    print("\n2. Endurance exercise simulation")
    simulate_exercise_session("running", 180, "moderate", True)
    
    # Simulate a HIIT exercise session
    print("\n3. HIIT exercise simulation")
    simulate_exercise_session("burpees", 150, "very_high", True)
