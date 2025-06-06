"""
Test script for Smart Orb stimulation controller

This script simulates various exercise scenarios and visualizes
the adaptive stimulation patterns generated by the controller.

Copyright (c) 2024 Ucaretron Inc.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os
import sys
from enum import Enum
import time
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the controller
from exercise_enhancement.stimulation_controller import StimulationController, ExercisePhase

class ExerciseSimulator:
    """
    Simulates exercise scenarios to test the Smart Orb controller
    """
    
    def __init__(self, user_profile=None, duration_minutes=30, output_dir='output'):
        """
        Initialize the simulator with user profile and exercise parameters
        
        Args:
            user_profile: Dictionary containing user information
            duration_minutes: Length of simulated exercise session in minutes
            output_dir: Directory to save output visualizations
        """
        self.controller = StimulationController(user_profile)
        self.duration = duration_minutes
        self.time_points = np.linspace(0, duration_minutes, duration_minutes * 60)  # 1 Hz sampling
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage
        self.heart_rate = np.zeros_like(self.time_points)
        self.emg_activity = np.zeros_like(self.time_points)
        self.acceleration = np.zeros_like(self.time_points)
        self.gsr = np.zeros_like(self.time_points)
        self.impedance = np.zeros_like(self.time_points)
        
        self.phase_history = []
        self.fatigue_history = np.zeros_like(self.time_points)
        self.intensity_history = np.zeros_like(self.time_points)
        
        # TENS parameters history
        self.tens_frequency = np.zeros_like(self.time_points)
        self.tens_intensity = np.zeros_like(self.time_points)
        self.tens_pulse_width = np.zeros_like(self.time_points)
        
        # Other stimulation parameters
        self.visual_brightness = np.zeros_like(self.time_points)
        self.audio_volume = np.zeros_like(self.time_points)
        self.haptic_intensity = np.zeros_like(self.time_points)
        self.thermal_temp = np.zeros_like(self.time_points)
        
        print(f"Initialized exercise simulator for {duration_minutes} minute session")

    def generate_standard_workout(self):
        """
        Generate a standard workout with warmup, main exercise, and cooldown
        """
        print("Generating standard workout pattern...")
        
        # Time markers for phase transitions (percentage of total duration)
        warmup_end = 0.15  # First 15% is warmup
        main_end = 0.75    # Next 60% is main exercise with increasing intensity
        peak_end = 0.85    # Next 10% is peak intensity
        # Remaining 15% is cooldown

        max_hr = self.controller.user_profile["max_heart_rate"]
        rest_hr = self.controller.user_profile["resting_heart_rate"]
        
        # Generate heart rate profile
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            if normalized_time <= warmup_end:
                # Warmup: Heart rate increases linearly
                hr_pct = normalized_time / warmup_end * 0.5  # Up to 50% of reserve
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            elif normalized_time <= main_end:
                # Main exercise: Heart rate varies with some intervals
                main_phase_time = (normalized_time - warmup_end) / (main_end - warmup_end)
                
                # Add some intervals for realism
                interval_effect = 0.1 * np.sin(main_phase_time * 2 * np.pi * 4)
                
                hr_pct = 0.5 + main_phase_time * 0.3 + interval_effect  # 50-80% with intervals
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            elif normalized_time <= peak_end:
                # Peak effort: High heart rate
                peak_phase_time = (normalized_time - main_end) / (peak_end - main_end)
                hr_pct = 0.8 + peak_phase_time * 0.15  # 80-95%
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            else:
                # Cooldown: Heart rate decreases exponentially
                cooldown_phase_time = (normalized_time - peak_end) / (1.0 - peak_end)
                hr_pct = 0.95 * np.exp(-3 * cooldown_phase_time)  # Exponential decrease
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
        
        # Generate EMG activity (roughly correlates with heart rate but with more variation)
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # Base EMG follows heart rate with normalized scale
            hr_normalized = (self.heart_rate[i] - rest_hr) / (max_hr - rest_hr)
            
            # Add more randomness to EMG
            noise = 0.15 * np.random.randn()
            
            # Add fatigue effect - EMG amplitude decreases as workout progresses
            fatigue_effect = 0.2 * normalized_time if normalized_time <= peak_end else 0.2
            
            self.emg_activity[i] = min(1.0, max(0.0, hr_normalized + noise - fatigue_effect))
        
        # Generate acceleration data (movement intensity)
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            if normalized_time <= warmup_end:
                # Warmup: Gradually increasing movement
                self.acceleration[i] = 0.5 * (normalized_time / warmup_end)
                
            elif normalized_time <= main_end:
                # Main exercise: Moderate with intervals
                main_phase_time = (normalized_time - warmup_end) / (main_end - warmup_end)
                interval_effect = 0.3 * np.sin(main_phase_time * 2 * np.pi * 5)
                self.acceleration[i] = 0.5 + 0.3 * main_phase_time + interval_effect
                
            elif normalized_time <= peak_end:
                # Peak: High intensity movement
                self.acceleration[i] = 0.8 + 0.2 * np.random.rand()
                
            else:
                # Cooldown: Decreasing movement
                cooldown_phase_time = (normalized_time - peak_end) / (1.0 - peak_end)
                self.acceleration[i] = 0.8 * (1 - cooldown_phase_time)
        
        # Generate GSR data (stress response)
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # GSR follows heart rate with lag and smoothing
            if i > 60:  # 1-minute lag
                hr_normalized = (self.heart_rate[i-60] - rest_hr) / (max_hr - rest_hr)
                self.gsr[i] = 0.8 * self.gsr[i-1] + 0.2 * hr_normalized
            else:
                hr_normalized = (self.heart_rate[i] - rest_hr) / (max_hr - rest_hr)
                self.gsr[i] = 0.3 * hr_normalized
        
        # Generate impedance data (approximation of hydration changes)
        # Higher values = better hydration, decreases during exercise
        start_impedance = 500  # Starting value
        min_impedance = 450    # Minimum value
        
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # Impedance decreases as workout progresses (dehydration)
            impedance_drop = (start_impedance - min_impedance) * (
                0.7 * min(1.0, normalized_time * 2) +  # Main decrease
                0.3 * (1 - np.exp(-normalized_time * 3))  # Exponential component
            )
            
            # Add small random fluctuations
            noise = 3 * np.random.randn()
            
            self.impedance[i] = start_impedance - impedance_drop + noise
            
        print("Standard workout pattern generated")
        return self

    def generate_hiit_workout(self):
        """
        Generate a high-intensity interval training workout
        """
        print("Generating HIIT workout pattern...")
        
        # Time markers for phase transitions (percentage of total duration)
        warmup_end = 0.1   # First 10% is warmup
        main_end = 0.9     # Next 80% is intervals
        # Remaining 10% is cooldown

        max_hr = self.controller.user_profile["max_heart_rate"]
        rest_hr = self.controller.user_profile["resting_heart_rate"]
        
        # HIIT parameters
        interval_count = 8
        work_duration = 0.6  # minutes
        rest_duration = 1.0  # minutes
        
        # Generate heart rate profile
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            if normalized_time <= warmup_end:
                # Warmup: Heart rate increases linearly
                hr_pct = normalized_time / warmup_end * 0.5  # Up to 50% of reserve
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            elif normalized_time <= main_end:
                # HIIT intervals
                main_phase_time = t - (warmup_end * self.duration)
                cycle_duration = work_duration + rest_duration
                cycle_position = main_phase_time % cycle_duration
                
                if cycle_position < work_duration:
                    # High intensity interval
                    interval_position = cycle_position / work_duration
                    hr_pct = 0.7 + 0.25 * (1 - np.exp(-3 * interval_position))  # Quick rise to 95%
                else:
                    # Recovery between intervals
                    recovery_position = (cycle_position - work_duration) / rest_duration
                    hr_pct = 0.7 * np.exp(-2 * recovery_position) + 0.4  # Exponential decrease to 40%
                
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            else:
                # Cooldown: Heart rate decreases exponentially
                cooldown_phase_time = (normalized_time - main_end) / (1.0 - main_end)
                hr_pct = 0.7 * np.exp(-3 * cooldown_phase_time)  # Exponential decrease
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
        
        # Generate EMG activity with higher peaks during intervals
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # Base EMG follows heart rate with normalized scale
            hr_normalized = (self.heart_rate[i] - rest_hr) / (max_hr - rest_hr)
            
            # Add more randomness to EMG
            noise = 0.1 * np.random.randn()
            
            # Add fatigue effect - EMG amplitude decreases as workout progresses
            # Stronger fatigue effect in HIIT
            fatigue_effect = 0.3 * normalized_time if normalized_time <= main_end else 0.3
            
            # HIIT has higher muscle activation during intervals
            intensity_boost = 0.0
            if warmup_end < normalized_time <= main_end:
                main_phase_time = t - (warmup_end * self.duration)
                cycle_duration = work_duration + rest_duration
                cycle_position = main_phase_time % cycle_duration
                
                if cycle_position < work_duration:
                    # Boost during high intensity intervals
                    intensity_boost = 0.2
            
            self.emg_activity[i] = min(1.0, max(0.0, hr_normalized + noise - fatigue_effect + intensity_boost))
        
        # Generate acceleration data with high burst during intervals
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            if normalized_time <= warmup_end:
                # Warmup: Gradually increasing movement
                self.acceleration[i] = 0.5 * (normalized_time / warmup_end)
                
            elif normalized_time <= main_end:
                # HIIT intervals
                main_phase_time = t - (warmup_end * self.duration)
                cycle_duration = work_duration + rest_duration
                cycle_position = main_phase_time % cycle_duration
                
                if cycle_position < work_duration:
                    # High intensity interval
                    self.acceleration[i] = 1.5 + 0.3 * np.random.rand()
                else:
                    # Recovery
                    self.acceleration[i] = 0.3 + 0.2 * np.random.rand()
                
            else:
                # Cooldown: Decreasing movement
                cooldown_phase_time = (normalized_time - main_end) / (1.0 - main_end)
                self.acceleration[i] = 0.5 * (1 - cooldown_phase_time)
        
        # Generate GSR data (stress response)
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # GSR follows heart rate with lag and smoothing
            if i > 30:  # 30-second lag (shorter for HIIT)
                hr_normalized = (self.heart_rate[i-30] - rest_hr) / (max_hr - rest_hr)
                self.gsr[i] = 0.7 * self.gsr[i-1] + 0.3 * hr_normalized
            else:
                hr_normalized = (self.heart_rate[i] - rest_hr) / (max_hr - rest_hr)
                self.gsr[i] = 0.3 * hr_normalized
        
        # Generate impedance data (approximation of hydration changes)
        # Higher values = better hydration, decreases during exercise
        # HIIT causes faster dehydration
        start_impedance = 500  # Starting value
        min_impedance = 430    # Lower minimum value for HIIT
        
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # Impedance decreases as workout progresses (dehydration)
            impedance_drop = (start_impedance - min_impedance) * (
                0.8 * min(1.0, normalized_time * 2.5) +  # Faster decrease
                0.2 * (1 - np.exp(-normalized_time * 4))  # Exponential component
            )
            
            # Add small random fluctuations
            noise = 3 * np.random.randn()
            
            self.impedance[i] = start_impedance - impedance_drop + noise
            
        print("HIIT workout pattern generated")
        return self
    
    def generate_endurance_workout(self):
        """
        Generate a long steady-state endurance workout
        """
        print("Generating endurance workout pattern...")
        
        # Time markers for phase transitions (percentage of total duration)
        warmup_end = 0.1   # First 10% is warmup
        main_end = 0.85    # Next 75% is steady-state
        # Remaining 15% is cooldown

        max_hr = self.controller.user_profile["max_heart_rate"]
        rest_hr = self.controller.user_profile["resting_heart_rate"]
        
        # Target heart rate for endurance (60-70% of max)
        target_hr_pct = 0.65
        target_hr = rest_hr + target_hr_pct * (max_hr - rest_hr)
        
        # Generate heart rate profile
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            if normalized_time <= warmup_end:
                # Warmup: Heart rate increases linearly
                hr_pct = normalized_time / warmup_end * target_hr_pct  # Up to target
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            elif normalized_time <= main_end:
                # Steady state with small variations
                main_phase_time = (normalized_time - warmup_end) / (main_end - warmup_end)
                
                # Add gentle undulations for realism
                undulation = 0.05 * np.sin(main_phase_time * 2 * np.pi * 3)
                
                # Add slight drift upward due to cardiac drift
                drift = 0.05 * main_phase_time
                
                hr_pct = target_hr_pct + undulation + drift
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
                
            else:
                # Cooldown: Heart rate decreases exponentially
                cooldown_phase_time = (normalized_time - main_end) / (1.0 - main_end)
                hr_pct = (target_hr_pct + 0.05) * np.exp(-2 * cooldown_phase_time)  # Exponential decrease
                self.heart_rate[i] = rest_hr + hr_pct * (max_hr - rest_hr)
        
        # Generate EMG activity (moderate and steady)
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # Base EMG follows heart rate with normalized scale
            hr_normalized = (self.heart_rate[i] - rest_hr) / (max_hr - rest_hr)
            
            # Add small randomness to EMG
            noise = 0.05 * np.random.randn()
            
            # Add fatigue effect - EMG amplitude decreases more in endurance
            fatigue_effect = 0.4 * normalized_time if normalized_time <= main_end else 0.4
            
            self.emg_activity[i] = min(1.0, max(0.0, hr_normalized + noise - fatigue_effect))
        
        # Generate acceleration data (steady and rhythmic)
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            if normalized_time <= warmup_end:
                # Warmup: Gradually increasing movement
                self.acceleration[i] = 0.3 * (normalized_time / warmup_end) + 0.1 * np.sin(t * 10)
                
            elif normalized_time <= main_end:
                # Steady-state rhythmic movement
                self.acceleration[i] = 0.4 + 0.1 * np.sin(t * 10)  # Rhythmic component
                
            else:
                # Cooldown: Decreasing movement
                cooldown_phase_time = (normalized_time - main_end) / (1.0 - main_end)
                self.acceleration[i] = (0.4 + 0.1 * np.sin(t * 10)) * (1 - cooldown_phase_time)
        
        # Generate GSR data (stress response) - lower for endurance
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # GSR follows heart rate with lag and smoothing
            if i > 120:  # 2-minute lag (longer for endurance)
                hr_normalized = (self.heart_rate[i-120] - rest_hr) / (max_hr - rest_hr)
                self.gsr[i] = 0.9 * self.gsr[i-1] + 0.1 * hr_normalized
            else:
                hr_normalized = (self.heart_rate[i] - rest_hr) / (max_hr - rest_hr)
                self.gsr[i] = 0.2 * hr_normalized
        
        # Generate impedance data (approximation of hydration changes)
        # Higher values = better hydration, decreases during exercise
        # Endurance causes more severe dehydration due to duration
        start_impedance = 500  # Starting value
        min_impedance = 420    # Lower minimum value for endurance
        
        for i, t in enumerate(self.time_points):
            normalized_time = t / self.duration
            
            # Impedance decreases as workout progresses (dehydration)
            impedance_drop = (start_impedance - min_impedance) * (
                0.6 * min(1.0, normalized_time * 1.5) +  # Slower initial decrease
                0.4 * (1 - np.exp(-normalized_time * 2))  # Exponential component
            )
            
            # Add small random fluctuations
            noise = 2 * np.random.randn()
            
            self.impedance[i] = start_impedance - impedance_drop + noise
            
        print("Endurance workout pattern generated")
        return self
    
    def run_simulation(self):
        """
        Run the simulation by processing all time points through the controller
        """
        print("Running simulation through stimulation controller...")
        
        # Process each time point
        for i, t in enumerate(self.time_points):
            # Skip some points for speed (process every 10th point)
            if i % 10 != 0 and i != len(self.time_points) - 1:
                continue
                
            # Update controller with current physiological state
            state = self.controller.update_physiological_state(
                heart_rate=self.heart_rate[i],
                emg_activity=self.emg_activity[i],
                gsr=self.gsr[i],
                acceleration=self.acceleration[i],
                impedance_data=self.impedance[i]
            )
            
            # Get stimulation parameters
            params = self.controller.adjust_stimulation()
            
            # Record state and parameters
            self.phase_history.append(state["phase"])
            self.fatigue_history[i] = state["fatigue"]
            self.intensity_history[i] = state["intensity"]
            
            # Record TENS parameters
            self.tens_frequency[i] = params["tens"]["frequency"]
            self.tens_intensity[i] = params["tens"]["intensity"]
            self.tens_pulse_width[i] = params["tens"]["pulse_width"]
            
            # Record other stimulation parameters
            self.visual_brightness[i] = params["visual"]["brightness"]
            self.audio_volume[i] = params["audio"]["volume"]
            self.haptic_intensity[i] = params["haptic"]["intensity"]
            self.thermal_temp[i] = params["thermal"]["temperature"]
            
            # Print progress
            if i % 300 == 0:  # Every 5 minutes
                minutes = int(t)
                print(f"Processed {minutes} minutes. Phase: {state['phase'].name}, Fatigue: {state['fatigue']:.2f}")
        
        print("Simulation complete")
        return self
    
    def visualize_results(self, title="Smart Orb Simulation Results"):
        """
        Generate visualizations of the simulation results
        
        Args:
            title: Title for the visualization
            
        Returns:
            str: Path to saved visualization file
        """
        print("Generating visualizations...")
        
        # Create figure
        plt.figure(figsize=(15, 12))
        gs = GridSpec(5, 2, figure=plt.gcf())
        
        # Convert phase history to numeric for plotting
        phase_numeric = np.zeros_like(self.time_points)
        for i, phase in enumerate(self.phase_history):
            idx = i * 10  # Because we processed every 10th point
            if idx < len(phase_numeric):
                phase_numeric[idx] = phase.value
        
        # Interpolate values at skipped points
        from scipy.interpolate import interp1d
        valid_indices = np.where(phase_numeric != 0)[0]
        if len(valid_indices) > 1:  # Need at least 2 points for interpolation
            f = interp1d(valid_indices, phase_numeric[valid_indices], kind='previous', 
                         bounds_error=False, fill_value=phase_numeric[valid_indices[0]])
            all_indices = np.arange(len(phase_numeric))
            phase_numeric = f(all_indices)
        
        # Plot physiological signals
        ax1 = plt.subplot(gs[0, 0])
        ax1.plot(self.time_points, self.heart_rate, 'r-', label='Heart Rate (BPM)')
        ax1.set_ylabel('Heart Rate (BPM)')
        ax1.set_ylim(self.controller.user_profile["resting_heart_rate"] - 10, 
                    self.controller.user_profile["max_heart_rate"] + 10)
        ax1.set_title('Physiological Signals')
        ax1.grid(True)
        
        ax2 = plt.subplot(gs[1, 0], sharex=ax1)
        ax2.plot(self.time_points, self.emg_activity, 'g-', label='EMG Activity')
        ax2.set_ylabel('EMG Activity')
        ax2.set_ylim(0, 1.1)
        ax2.grid(True)
        
        ax3 = plt.subplot(gs[2, 0], sharex=ax1)
        ax3.plot(self.time_points, self.acceleration, 'b-', label='Acceleration')
        ax3.set_ylabel('Acceleration')
        ax3.set_ylim(0, 2.0)
        ax3.grid(True)
        
        ax4 = plt.subplot(gs[3, 0], sharex=ax1)
        ax4.plot(self.time_points, self.gsr, 'm-', label='GSR')
        ax4.set_ylabel('GSR')
        ax4.set_ylim(0, 1.1)
        ax4.grid(True)
        
        ax5 = plt.subplot(gs[4, 0], sharex=ax1)
        ax5.plot(self.time_points, self.impedance, 'k-', label='Impedance')
        ax5.set_ylabel('Impedance')
        ax5.set_xlabel('Time (minutes)')
        ax5.set_ylim(400, 520)
        ax5.grid(True)
        
        # Plot exercise phases and controller outputs
        ax6 = plt.subplot(gs[0, 1])
        ax6.plot(self.time_points, phase_numeric, 'c-', linewidth=2)
        ax6.set_ylabel('Exercise Phase')
        ax6.set_yticks(range(5))
        ax6.set_yticklabels(['Warmup', 'Main', 'Peak', 'Cooldown', 'Recovery'])
        ax6.set_title('Controller Response')
        ax6.grid(True)
        
        ax7 = plt.subplot(gs[1, 1], sharex=ax6)
        ax7.plot(self.time_points, self.fatigue_history, 'r-', label='Fatigue')
        ax7.plot(self.time_points, self.intensity_history, 'b-', label='Intensity')
        ax7.set_ylabel('Level')
        ax7.set_ylim(0, 1.1)
        ax7.legend()
        ax7.grid(True)
        
        # Plot TENS parameters
        ax8 = plt.subplot(gs[2, 1], sharex=ax6)
        ax8.plot(self.time_points, self.tens_frequency, 'g-', label='Frequency')
        ax8_twin = ax8.twinx()
        ax8_twin.plot(self.time_points, self.tens_intensity * 100, 'r-', label='Intensity %')
        ax8.set_ylabel('TENS Frequency (Hz)')
        ax8_twin.set_ylabel('TENS Intensity (%)')
        ax8.set_ylim(0, 60)
        ax8_twin.set_ylim(0, 100)
        ax8.grid(True)
        
        # Create custom legend
        lines1, labels1 = ax8.get_legend_handles_labels()
        lines2, labels2 = ax8_twin.get_legend_handles_labels()
        ax8.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Plot other stimulation parameters
        ax9 = plt.subplot(gs[3, 1], sharex=ax6)
        ax9.plot(self.time_points, self.visual_brightness * 100, 'b-', label='Visual')
        ax9.plot(self.time_points, self.audio_volume * 100, 'g-', label='Audio')
        ax9.plot(self.time_points, self.haptic_intensity * 100, 'r-', label='Haptic')
        ax9.set_ylabel('Intensity (%)')
        ax9.set_ylim(0, 100)
        ax9.legend()
        ax9.grid(True)
        
        ax10 = plt.subplot(gs[4, 1], sharex=ax6)
        ax10.plot(self.time_points, self.thermal_temp, 'c-')
        ax10.set_ylabel('Temperature (°C)')
        ax10.set_xlabel('Time (minutes)')
        ax10.set_ylim(25, 37)
        ax10.grid(True)
        
        # Set common x-axis properties
        for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax10]:
            ax.set_xlim(0, self.duration)
        
        plt.tight_layout()
        plt.suptitle(title, fontsize=16, y=1.02)
        
        # Save the figure
        filename = f"{title.replace(' ', '_').lower()}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to {filepath}")
        
        return filepath
    
    def save_simulation_data(self):
        """
        Save the simulation data to a JSON file
        
        Returns:
            str: Path to saved data file
        """
        # Create a simplified data structure (not all points)
        sample_rate = 60  # Save one point per minute
        
        data = {
            "duration_minutes": self.duration,
            "user_profile": self.controller.user_profile,
            "time_points": self.time_points[::sample_rate].tolist(),
            "physiological_data": {
                "heart_rate": self.heart_rate[::sample_rate].tolist(),
                "emg_activity": self.emg_activity[::sample_rate].tolist(),
                "gsr": self.gsr[::sample_rate].tolist(),
                "acceleration": self.acceleration[::sample_rate].tolist(),
                "impedance": self.impedance[::sample_rate].tolist()
            },
            "controller_output": {
                "fatigue": self.fatigue_history[::sample_rate].tolist(),
                "intensity": self.intensity_history[::sample_rate].tolist(),
                "tens_frequency": self.tens_frequency[::sample_rate].tolist(),
                "tens_intensity": self.tens_intensity[::sample_rate].tolist(),
                "tens_pulse_width": self.tens_pulse_width[::sample_rate].tolist(),
                "visual_brightness": self.visual_brightness[::sample_rate].tolist(),
                "audio_volume": self.audio_volume[::sample_rate].tolist(),
                "haptic_intensity": self.haptic_intensity[::sample_rate].tolist(),
                "thermal_temp": self.thermal_temp[::sample_rate].tolist()
            }
        }
        
        # Save phases as strings
        phase_strings = []
        for i, phase in enumerate(self.phase_history):
            if i * 10 % sample_rate == 0 and i * 10 < len(self.time_points):
                phase_strings.append(phase.name)
        
        data["controller_output"]["phase"] = phase_strings
        
        # Save to file
        filename = f"simulation_data_{int(time.time())}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Simulation data saved to {filepath}")
        return filepath

def run_standard_workout_simulation():
    """Run a simulation of a standard workout"""
    user_profile = {
        "max_heart_rate": 185,
        "resting_heart_rate": 62,
        "max_tens_intensity": 0.7,
        "preferred_audio": "forest",
        "preferred_color": "blue",
        "skin_sensitivity": "normal",
        "fatigue_threshold": 0.8
    }
    
    simulator = ExerciseSimulator(user_profile, duration_minutes=45)
    simulator.generate_standard_workout().run_simulation()
    simulator.visualize_results("Standard Workout Simulation")
    simulator.save_simulation_data()
    
def run_hiit_workout_simulation():
    """Run a simulation of a HIIT workout"""
    user_profile = {
        "max_heart_rate": 190,
        "resting_heart_rate": 65,
        "max_tens_intensity": 0.8,
        "preferred_audio": "electronic",
        "preferred_color": "red",
        "skin_sensitivity": "low",
        "fatigue_threshold": 0.9
    }
    
    simulator = ExerciseSimulator(user_profile, duration_minutes=30)
    simulator.generate_hiit_workout().run_simulation()
    simulator.visualize_results("HIIT Workout Simulation")
    simulator.save_simulation_data()
    
def run_endurance_workout_simulation():
    """Run a simulation of an endurance workout"""
    user_profile = {
        "max_heart_rate": 180,
        "resting_heart_rate": 58,
        "max_tens_intensity": 0.6,
        "preferred_audio": "ambient",
        "preferred_color": "green",
        "skin_sensitivity": "normal",
        "fatigue_threshold": 0.7
    }
    
    simulator = ExerciseSimulator(user_profile, duration_minutes=90)
    simulator.generate_endurance_workout().run_simulation()
    simulator.visualize_results("Endurance Workout Simulation")
    simulator.save_simulation_data()

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Run the simulations
    print("\n=== Running Standard Workout Simulation ===")
    run_standard_workout_simulation()
    
    print("\n=== Running HIIT Workout Simulation ===")
    run_hiit_workout_simulation()
    
    print("\n=== Running Endurance Workout Simulation ===")
    run_endurance_workout_simulation()
    
    print("\nAll simulations complete. Results saved to the 'output' directory.")
