# Smart Orb

An advanced wearable smart device for exercise enhancement using electrochemical impedance and TENS-based multi-sensory integrated neuro-modulation.

<p align="center">
  <img src="https://raw.githubusercontent.com/JJshome/Smart-Orb/main/code/web_dashboard/static/smart_orb_animation.svg" alt="Smart Orb Animation" width="600">
</p>

> **IMPORTANT INTELLECTUAL PROPERTY NOTICE**: The Smart Orb technology described in this repository is based on patent-pending technology owned by Ucaretron Inc. (Patent Application No. KR10-2024-0071235). While the software code in this repository is available under the MIT License, the underlying technology, methodologies, and processes described herein are proprietary to Ucaretron Inc. and may not be used for commercial purposes without explicit written permission. All rights related to the core Smart Orb technology are reserved by Ucaretron Inc.

## Overview

Smart Orb is a spherical handheld device that integrates multiple sensing and stimulation technologies to enhance physical performance, facilitate recovery, and improve overall well-being. This device leverages electrochemical impedance measurement and transcutaneous electrical nerve stimulation (TENS) along with multi-sensory feedback to provide a comprehensive neuro-modulation solution.

## Interactive Web Demo

Experience the Smart Orb's capabilities through our interactive web simulation. The web dashboard allows you to:

- Simulate various exercise scenarios with different intensity levels
- Visualize real-time physiological signals (heart rate, EMG, acceleration)
- See how TENS parameters adapt to exercise phases
- Explore different user profiles and their personalized stimulation patterns

### Running the Web Demo

#### Method 1: Direct Python Execution

```bash
# Clone the repository
git clone https://github.com/JJshome/Smart-Orb.git
cd Smart-Orb

# Install requirements
pip install -r requirements.txt

# Launch the web dashboard
cd code/web_dashboard
python app.py
```

Then open your browser and go to: `http://localhost:5000`

#### Method 2: Docker Deployment (Recommended)

For the easiest deployment option, we provide Docker support:

```bash
# Clone the repository
git clone https://github.com/JJshome/Smart-Orb.git
cd Smart-Orb

# Build and start the container
docker-compose up -d

# The dashboard will be available at http://localhost:5000
```

This method ensures all dependencies are properly installed and isolated.

<p align="center">
  <img src="https://github.com/JJshome/Smart-Orb/assets/107289883/1a2a3456-0f8b-4c78-8d99-30d61c5e6de7" alt="Smart Orb Dashboard" width="700">
</p>

## Key Features

- **Multi-Sensory Integration**: Combines visual, auditory, tactile, and thermal stimulation for a holistic sensory experience
- **Electrochemical Impedance Analysis**: Real-time body composition and physiological state assessment
- **Adaptive TENS Stimulation**: Personalized electrical stimulation patterns tailored to individual needs and activities
- **AI-Powered Control System**: Edge AI processing for real-time adaptation to physiological signals
- **Wireless Connectivity**: Seamless integration with complementary body-worn sensors and stimulators

## Applications

- **Exercise Enhancement**: Optimize workout performance, improve muscle recruitment, and accelerate recovery
- **Pain Management**: Non-pharmaceutical approach to managing chronic and acute pain
- **Sleep Enhancement**: Facilitate deeper, more restorative sleep through targeted neuro-modulation
- **Stress Reduction**: Real-time stress monitoring and adaptive relaxation protocols

## Project Structure

```
Smart-Orb/
├── code/
│   ├── exercise_enhancement/
│   │   ├── data_generation.py        # Synthetic data generation for testing
│   │   ├── stimulation_controller.py # Core control logic for adaptive stimulation
│   │   └── test_stimulation_controller.py # Test script for simulation
│   ├── pain_management/
│   ├── sleep_enhancement/
│   ├── stress_reduction/
│   └── web_dashboard/               # Interactive web demonstration
│       ├── app.py                   # Flask application for web dashboard
│       ├── templates/               # HTML templates
│       └── static/                  # CSS, JS, and images
├── hardware/
│   ├── designs/
│   ├── firmware/
│   └── schematics/
├── research/
│   ├── literature/
│   └── protocols/
├── Dockerfile                       # Docker configuration
└── docker-compose.yml               # Docker Compose for easy deployment
```

## Technical Specifications

### Hardware Components

- **Sensors**:
  - PPG (photoplethysmography) for heart rate and SpO2
  - GSR (galvanic skin response) for stress monitoring
  - EMG (electromyography) for muscle activity
  - EEG (electroencephalography) for basic brain activity patterns
  - Electrochemical impedance sensors for body composition

- **Stimulation Elements**:
  - Micro LED array for visual stimulation
  - Microphone and speakers for audio feedback
  - High-resolution vibration motors for tactile feedback
  - Peltier elements for thermal stimulation
  - TENS electrodes for electrical nerve stimulation

- **Processing**:
  - Edge AI chip for real-time signal processing
  - Bluetooth 5.0 for wireless connectivity
  - Energy harvesting system for extended battery life

### Exercise Enhancement Module

The exercise enhancement module optimizes workout performance through:

1. **Real-time Exercise Detection**: Automatically identifies exercise type through motion patterns
2. **Adaptive Stimulation**: Adjusts stimulation parameters based on exercise phase (warmup, main, cooldown)
3. **Fatigue Management**: Modifies stimulation to compensate for muscle fatigue during extended workouts
4. **Recovery Optimization**: Specialized stimulation patterns to accelerate post-workout recovery

## Getting Started with Development

### Prerequisites

- Python 3.8+
- Required Python packages:
  - NumPy
  - Matplotlib
  - Joblib
  - pytest (for testing)
  - Flask (for web dashboard)
  - Plotly (for interactive charts)

### Installation

```bash
git clone https://github.com/JJshome/Smart-Orb.git
cd Smart-Orb
pip install -r requirements.txt
```

### Running the Simulation

```bash
cd code/exercise_enhancement
python test_stimulation_controller.py
```

This will run three different exercise simulations and generate visualization plots in the `output/` directory.

## How It Works

<p align="center">
  <img src="https://github.com/JJshome/Smart-Orb/assets/107289883/1a2a3456-0f8b-4c78-8d99-30d61c5e6de7" alt="Smart Orb Functionality" width="700">
</p>

1. The user holds the Smart Orb in their hand while wearing the wireless sensor/stimulation unit on the target body area
2. Real-time sensors continuously gather physiological data:
   - Heart rate and blood oxygen levels via PPG
   - Stress levels via GSR
   - Muscle activity via EMG
   - Body composition via electrochemical impedance
3. Edge AI processes this data to determine:
   - Current exercise type and intensity
   - Physiological state (stress, fatigue, etc.)
   - Optimal stimulation parameters
4. Adaptive stimulation is delivered through multiple sensory channels:
   - Visual feedback through color-changing LEDs
   - Audio stimulation via binaural beats and rhythmic cues
   - Tactile feedback through precision vibration patterns
   - TENS stimulation to target muscles for enhanced performance

## Deployment Options

### Local Development Server

For development and testing:

```bash
cd code/web_dashboard
python app.py
```

### Docker Container

For production or cross-platform deployment:

```bash
# Build the Docker image
docker build -t smart-orb-dashboard .

# Run the container
docker run -p 5000:5000 -d smart-orb-dashboard
```

### Docker Compose

For easy setup with proper volumes and environment:

```bash
docker-compose up -d
```

## Future Development

- Integration with real-time biometric sensors
- Mobile application for configuration and data visualization
- Cloud-based analytics for long-term performance tracking
- Additional modules for cognitive enhancement and meditation support

## Research Background

Smart Orb builds on extensive research in neurostimulation, electrochemical impedance analysis, and multi-sensory integration. Key findings from scientific literature demonstrate that:

- Multi-sensory stimulation produces stronger neural responses than single-modality stimulation
- Personalized TENS parameters based on individual physiology yield superior outcomes
- Closed-loop systems that adapt in real-time to physiological changes show improved efficacy

## Intellectual Property Statement

The Smart Orb technology is developed and owned by Ucaretron Inc., a company specializing in advanced digital therapeutics and neuro-modulation technologies. The core technology described in this repository is protected under Patent Application No. KR10-2024-0071235 ("Electrochemical Impedance and TENS-based Multi-Sensory Integrated Neuro-Modulation Wearable Smart Device and System").

### Rights Clarification:

- **Software Code**: The software code in this repository is released under the MIT License, allowing for modification, distribution, and use in both private and commercial software projects.
- **Core Technology**: The underlying technology, methodologies, processes, and hardware designs described in this repository are proprietary to Ucaretron Inc. and protected by pending patent applications. Commercial use of these aspects requires explicit permission from Ucaretron Inc.

For licensing inquiries or commercial use permissions, please contact: licensing@ucaretron.com

## Contributing

We welcome contributions to improve the software aspects of the Smart Orb system. Please see our [contributing guidelines](CONTRIBUTING.md) for details on how to get involved. Note that all contributors must acknowledge the intellectual property rights of Ucaretron Inc. regarding the core technology.

## License

The software code in this repository is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The Smart Orb technology, methodologies, and processes are proprietary to Ucaretron Inc. - all rights reserved.
