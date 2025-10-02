# Kitchen Display System (KDS)

A production-ready Kitchen Display System and TCP Printer Emulator built with Python and Kivy.

## Project Overview

This project provides a two-part solution for restaurant environments:
1. **TCP Printer Emulator (`printer.py`)**: Intercepts raw TCP print jobs (typically sent to port 9100) from Point of Sale (POS) systems and saves them as text/print files.
2. **Kitchen Display System (`kds.py`)**: A GUI application built with Kivy that polls the output directory, parses the raw receipt data into visual order tickets, tracks elapsed time, and allows kitchen staff to "bump" (complete) orders.

### Key Features
- **Real-time Order Parsing:** Automatically detects, reads, and parses incoming print files.
- **Visual Alert Timers:** Order tickets change color automatically (Green -> Yellow -> Red) based on configurable wait times.
- **TCP Print Interception:** Acts as a network printer to seamlessly integrate with legacy POS systems.
- **Responsive GUI:** Built with Kivy for cross-platform compatibility and touch-friendly interface.

## Tech Stack
- **Backend/Networking:** Python, Sockets, Threading
- **GUI Framework:** Kivy
- **Configuration:** python-dotenv

## Project Structure
```text
kds_portafolio/
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
├── src/                 # Application source code
│   ├── kds.py           # Kivy GUI Kitchen Display System
│   └── printer.py       # TCP Network Printer Emulator
├── tests/               # Unit and integration tests
└── assets/              # Static assets and UI resources
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Virtual Environment recommended.

### Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd kds_portafolio
   ```

2. **Set up a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env and supply your desired ports and directory paths.
   ```

### Usage

1. **Start the Printer Emulator:**
   Listen for incoming print jobs on the configured network port.
   ```bash
   python src/printer.py
   ```

2. **Start the KDS Dashboard:**
   Launch the graphical interface to view and manage orders.
   ```bash
   python src/kds.py
   ```

*Note: Send raw text payloads to the configured TCP port (default 9100) from your POS system or using a network utility like `netcat` to test.*
