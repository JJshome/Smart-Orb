"""
Smart Orb Web Dashboard

A Flask application for visualizing Smart Orb data and controlling
the device through an interactive web interface.

Copyright (c) 2024 Ucaretron Inc.
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import random
import time
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# Sample user profiles
USERS = {
    "user1": {
        "name": "Alex Kim",
        "age": 32,
        "weight": 75,
        "height": 178,
        "max_heart_rate": 188,
        "resting_heart_rate": 62,
        "max_tens_intensity": 0.7,
        "preferred_audio": "nature",
        "preferred_color": "blue",
        "skin_sensitivity": "normal",
        "exercise_type": "strength",
        "sessions": 24,
        "avatar": "user1.jpg"
    },
    "user2": {
        "name": "Jamie Chen",
        "age": 28,
        "weight": 63,
        "height": 165,
        "max_heart_rate": 192,
        "resting_heart_rate": 58,
        "max_tens_intensity": 0.8,
        "preferred_audio": "electronic",
        "preferred_color": "purple",
        "skin_sensitivity": "sensitive",
        "exercise_type": "cardio",
        "sessions": 17,
        "avatar": "user2.jpg"
    },
    "user3": {
        "name": "Taylor Smith",
        "age": 45,
        "weight": 82,
        "height": 183,
        "max_heart_rate": 175,
        "resting_heart_rate": 65,
        "max_tens_intensity": 0.6,
        "preferred_audio": "ambient",
        "preferred_color": "green",
        "skin_sensitivity": "normal",
        "exercise_type": "rehab",
        "sessions": 31,
        "avatar": "user3.jpg"
    }
}

# Exercise types with descriptions
EXERCISE_TYPES = {
    "strength": {
        "name": "Strength Training",
        "description": "Focus on building muscle mass and strength through resistance training.",
        "tens_profile": "High intensity pulses (80-100Hz) during contraction phases.",
        "sensory_profile": "Red visual cues, rhythmic audio patterns, strong haptic feedback."
    },
    "cardio": {
        "name": "Cardiovascular Training",
        "description": "Improve heart health and endurance through aerobic activities.",
        "tens_profile": "Medium frequency continuous stimulation (30-50Hz).",
        "sensory_profile": "Blue/green visuals, steady beat audio, moderate pulsed haptics."
    },
    "flexibility": {
        "name": "Flexibility & Mobility",
        "description": "Enhance range of motion and joint mobility.",
        "tens_profile": "Low frequency (2-10Hz) during stretching to relax muscles.",
        "sensory_profile": "Purple/blue visuals, ambient soundscapes, gentle haptics."
    },
    "rehab": {
        "name": "Rehabilitation",
        "description": "Recovery from injury or surgery with controlled movements.",
        "tens_profile": "Alternating frequencies (10-40Hz) with adaptive intensity.",
        "sensory_profile": "Green visuals, calming audio, precise localized haptics."
    },
    "hiit": {
        "name": "High-Intensity Interval Training",
        "description": "Short bursts of intense exercise alternated with recovery periods.",
        "tens_profile": "Alternating high (80-100Hz) and low (20-30Hz) frequencies.",
        "sensory_profile": "Red/orange during work intervals, blue during recovery, dynamic audio."
    }
}

# Sample session data
def generate_session_data(user_id, session_id):
    """Generate sample data for a specific exercise session"""
    user = USERS[user_id]
    exercise_type = user["exercise_type"]
    
    # Random session duration between 30-60 minutes
    duration = random.randint(30, 60)
    
    # Generate timestamps (one per minute)
    timestamps = [(datetime.now() - timedelta(days=session_id)).strftime("%Y-%m-%d %H:%M:%S")]
    for i in range(1, duration):
        timestamps.append((datetime.now() - timedelta(days=session_id) + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"))
    
    # Heart rate pattern depends on exercise type
    heart_rate = []
    rest_hr = user["resting_heart_rate"]
    max_hr = user["max_heart_rate"]
    
    if exercise_type == "strength":
        # Strength training: intervals with recovery
        for i in range(duration):
            if i < 5:  # Warmup
                hr = rest_hr + (max_hr - rest_hr) * 0.3 * (i / 5)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                hr = rest_hr + (max_hr - rest_hr) * 0.3 * (cool_idx / 5)
            else:  # Main workout
                cycle = i % 10
                if cycle < 3:  # High intensity
                    hr = rest_hr + (max_hr - rest_hr) * (0.6 + 0.1 * random.random())
                else:  # Recovery
                    hr = rest_hr + (max_hr - rest_hr) * (0.4 + 0.05 * random.random())
            heart_rate.append(round(hr))
    
    elif exercise_type == "cardio":
        # Cardio: steady state with small variations
        for i in range(duration):
            if i < 5:  # Warmup
                hr = rest_hr + (max_hr - rest_hr) * 0.4 * (i / 5)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                hr = rest_hr + (max_hr - rest_hr) * 0.4 * (cool_idx / 5)
            else:  # Main workout
                hr = rest_hr + (max_hr - rest_hr) * (0.6 + 0.05 * np.sin(i/5) + 0.03 * random.random())
            heart_rate.append(round(hr))
    
    elif exercise_type == "rehab":
        # Rehab: controlled lower intensity
        for i in range(duration):
            if i < 5:  # Warmup
                hr = rest_hr + (max_hr - rest_hr) * 0.2 * (i / 5)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                hr = rest_hr + (max_hr - rest_hr) * 0.2 * (cool_idx / 5)
            else:  # Main workout
                hr = rest_hr + (max_hr - rest_hr) * (0.3 + 0.1 * np.sin(i/8) + 0.02 * random.random())
            heart_rate.append(round(hr))
    
    else:  # Default/HIIT
        # HIIT pattern
        for i in range(duration):
            if i < 5:  # Warmup
                hr = rest_hr + (max_hr - rest_hr) * 0.3 * (i / 5)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                hr = rest_hr + (max_hr - rest_hr) * 0.3 * (cool_idx / 5)
            else:  # Main workout
                cycle = i % 6
                if cycle < 2:  # High intensity
                    hr = rest_hr + (max_hr - rest_hr) * (0.8 + 0.1 * random.random())
                else:  # Recovery
                    hr = rest_hr + (max_hr - rest_hr) * (0.5 + 0.05 * random.random())
            heart_rate.append(round(hr))
    
    # Generate EMG activity data based on heart rate
    emg = []
    for hr in heart_rate:
        hr_norm = (hr - rest_hr) / (max_hr - rest_hr)
        emg_val = hr_norm * 0.8 + 0.1 * random.random()
        emg.append(round(emg_val * 100))
    
    # Generate TENS parameters
    tens_frequency = []
    tens_intensity = []
    tens_pulse_width = []
    
    for i in range(duration):
        if exercise_type == "strength":
            if i < 5:  # Warmup
                tens_frequency.append(20 + i * 2)
                tens_intensity.append(int(30 + i * 4))
                tens_pulse_width.append(150 + i * 10)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                tens_frequency.append(20 + cool_idx * 2)
                tens_intensity.append(int(30 + cool_idx * 4))
                tens_pulse_width.append(150 + cool_idx * 10)
            else:
                cycle = i % 10
                if cycle < 3:  # Active
                    tens_frequency.append(80 + random.randint(-5, 5))
                    tens_intensity.append(70 + random.randint(-5, 5))
                    tens_pulse_width.append(250 + random.randint(-10, 10))
                else:  # Recovery
                    tens_frequency.append(40 + random.randint(-5, 5))
                    tens_intensity.append(40 + random.randint(-5, 5))
                    tens_pulse_width.append(200 + random.randint(-10, 10))
        
        elif exercise_type == "cardio":
            if i < 5:  # Warmup
                tens_frequency.append(15 + i * 3)
                tens_intensity.append(int(25 + i * 3))
                tens_pulse_width.append(150 + i * 10)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                tens_frequency.append(15 + cool_idx * 3)
                tens_intensity.append(int(25 + cool_idx * 3))
                tens_pulse_width.append(150 + cool_idx * 10)
            else:
                tens_frequency.append(40 + 5 * np.sin(i/5) + random.randint(-3, 3))
                tens_intensity.append(50 + int(5 * np.sin(i/5)) + random.randint(-3, 3))
                tens_pulse_width.append(200 + random.randint(-10, 10))
        
        elif exercise_type == "rehab":
            if i < 5:  # Warmup
                tens_frequency.append(5 + i * 1)
                tens_intensity.append(int(20 + i * 2))
                tens_pulse_width.append(200 + i * 10)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                tens_frequency.append(5 + cool_idx * 1)
                tens_intensity.append(int(20 + cool_idx * 2))
                tens_pulse_width.append(200 + cool_idx * 10)
            else:
                tens_frequency.append(10 + 20 * np.sin(i/8) + random.randint(-2, 2))
                tens_intensity.append(30 + int(10 * np.sin(i/8)) + random.randint(-2, 2))
                tens_pulse_width.append(250 + random.randint(-10, 10))
        
        else:  # Default/HIIT
            if i < 5:  # Warmup
                tens_frequency.append(10 + i * 4)
                tens_intensity.append(int(20 + i * 4))
                tens_pulse_width.append(150 + i * 10)
            elif i > duration - 5:  # Cooldown
                cool_idx = duration - i
                tens_frequency.append(10 + cool_idx * 4)
                tens_intensity.append(int(20 + cool_idx * 4))
                tens_pulse_width.append(150 + cool_idx * 10)
            else:
                cycle = i % 6
                if cycle < 2:  # High intensity
                    tens_frequency.append(90 + random.randint(-5, 5))
                    tens_intensity.append(80 + random.randint(-5, 5))
                    tens_pulse_width.append(200 + random.randint(-10, 10))
                else:  # Recovery
                    tens_frequency.append(30 + random.randint(-5, 5))
                    tens_intensity.append(40 + random.randint(-5, 5))
                    tens_pulse_width.append(250 + random.randint(-10, 10))
    
    # Calculate calories burned (simplified model)
    weight_kg = user["weight"]
    age = user["age"]
    gender_factor = 0.9  # Simplified factor
    
    # MET values by exercise type (simplified)
    met_values = {
        "strength": 5.0,
        "cardio": 7.0,
        "flexibility": 3.0,
        "rehab": 3.5,
        "hiit": 8.0
    }
    
    met = met_values.get(exercise_type, 5.0)
    calories_per_minute = (met * 3.5 * weight_kg * gender_factor) / 200
    total_calories = round(calories_per_minute * duration)
    
    # Calculate metrics
    avg_heart_rate = round(sum(heart_rate) / len(heart_rate))
    max_heart_rate_session = max(heart_rate)
    hr_zone_minutes = {
        "easy": 0,
        "fat_burn": 0,
        "cardio": 0,
        "peak": 0
    }
    
    for hr in heart_rate:
        hr_percent = (hr - rest_hr) / (max_hr - rest_hr)
        if hr_percent < 0.6:
            hr_zone_minutes["easy"] += 1
        elif hr_percent < 0.7:
            hr_zone_minutes["fat_burn"] += 1
        elif hr_percent < 0.8:
            hr_zone_minutes["cardio"] += 1
        else:
            hr_zone_minutes["peak"] += 1
    
    # Effectiveness score (0-100)
    effectiveness = random.randint(80, 98)
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "user_name": user["name"],
        "date": (datetime.now() - timedelta(days=session_id)).strftime("%Y-%m-%d"),
        "duration": duration,
        "exercise_type": exercise_type,
        "timestamps": timestamps,
        "heart_rate": heart_rate,
        "emg": emg,
        "tens_frequency": tens_frequency,
        "tens_intensity": tens_intensity,
        "tens_pulse_width": tens_pulse_width,
        "calories": total_calories,
        "avg_heart_rate": avg_heart_rate,
        "max_heart_rate": max_heart_rate_session,
        "hr_zone_minutes": hr_zone_minutes,
        "effectiveness": effectiveness
    }

def get_user_sessions(user_id, count=5):
    """Get the most recent sessions for a user"""
    sessions = []
    for i in range(1, count+1):
        sessions.append(generate_session_data(user_id, i))
    return sessions

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html', users=USERS)

@app.route('/user/<user_id>')
def user_profile(user_id):
    """Render the user profile page"""
    if user_id not in USERS:
        return "User not found", 404
    
    user = USERS[user_id]
    exercise_type = EXERCISE_TYPES.get(user["exercise_type"], EXERCISE_TYPES["cardio"])
    sessions = get_user_sessions(user_id, 5)
    
    return render_template(
        'user_profile.html',
        user=user,
        user_id=user_id,
        exercise_type=exercise_type,
        sessions=sessions
    )

@app.route('/api/session/<user_id>/<int:session_id>')
def api_session(user_id, session_id):
    """API endpoint to get session data"""
    if user_id not in USERS:
        return jsonify({"error": "User not found"}), 404
    
    session_data = generate_session_data(user_id, session_id)
    return jsonify(session_data)

@app.route('/api/user/<user_id>/sessions')
def api_user_sessions(user_id):
    """API endpoint to get a user's session summaries"""
    if user_id not in USERS:
        return jsonify({"error": "User not found"}), 404
    
    count = request.args.get('count', 10, type=int)
    sessions = []
    
    for i in range(1, count+1):
        session_data = generate_session_data(user_id, i)
        # Simplify for summary view
        sessions.append({
            "session_id": session_data["session_id"],
            "date": session_data["date"],
            "duration": session_data["duration"],
            "exercise_type": session_data["exercise_type"],
            "calories": session_data["calories"],
            "avg_heart_rate": session_data["avg_heart_rate"],
            "effectiveness": session_data["effectiveness"]
        })
    
    return jsonify(sessions)

@app.route('/api/exercise_types')
def api_exercise_types():
    """API endpoint to get exercise type information"""
    return jsonify(EXERCISE_TYPES)

@app.route('/session/<user_id>/<int:session_id>')
def session_details(user_id, session_id):
    """Render the session details page"""
    if user_id not in USERS:
        return "User not found", 404
    
    user = USERS[user_id]
    session_data = generate_session_data(user_id, session_id)
    exercise_type = EXERCISE_TYPES.get(session_data["exercise_type"], EXERCISE_TYPES["cardio"])
    
    return render_template(
        'session_details.html',
        user=user,
        user_id=user_id,
        session=session_data,
        exercise_type=exercise_type
    )

@app.route('/device_control')
def device_control():
    """Render the device control page"""
    return render_template('device_control.html', users=USERS, exercise_types=EXERCISE_TYPES)

@app.route('/api/device/status')
def api_device_status():
    """API endpoint to get device status"""
    # Simulate device status information
    return jsonify({
        "connected": True,
        "battery_level": random.randint(60, 100),
        "firmware_version": "v2.3.1",
        "signal_strength": random.randint(70, 100),
        "temperature": round(36.5 + random.random() * 0.5, 1),
        "last_sync": (datetime.now() - timedelta(minutes=random.randint(5, 60))).strftime("%Y-%m-%d %H:%M")
    })

@app.route('/api/device/control', methods=['POST'])
def api_device_control():
    """API endpoint to control the device"""
    data = request.json
    
    # Simulate processing the control command
    command = data.get('command', '')
    parameters = data.get('parameters', {})
    
    time.sleep(0.5)  # Simulate processing time
    
    # Return a success response with confirmation
    return jsonify({
        "status": "success",
        "message": f"Command '{command}' executed successfully",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "parameters_received": parameters
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
