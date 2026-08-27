# ♻️ EcoReward System - Reverse Vending Machine Backend

EcoReward is a Python-based backend software system designed for Reverse Vending Machines (RVM). It tracks user recycling activities, calculates reward points based on deposited materials, manages recycling locations, displays real-time analytics, and exports structured business reports to Excel.

---

## 🏗️ System Architecture & Project Structure

The project follows a modular, layer-based architecture for scalability and clean code separation:

```text
EcoReward/
│
├── storage.py           # Core Data Layer: General-purpose JSON Reader/Writer
├── mapping.py           # Geospatial Layer: GPS location fetching, distance calculation, Folium live map
├── analytics.py         # Analytics Engine: Terminal dashboard and real-time metric computations
├── excel_reports.py     # Reporting Layer: Multi-sheet Excel workbook generator using pandas
├── main.py              # System Integrator: Main application CLI menu and flow controller
│
├── reports/             # Output directory for generated Excel reports (*.xlsx)
└── data/                # JSON Data storage directory (users, transactions, machines, etc.)