"""
Flask API Server for Airport Terminal Simulation Forecast
Provides real-time passenger forecast data to the simulation UI
"""

from flask import Flask, jsonify, render_template_string, send_file
from flask_cors import CORS
from forecast import PassengerForecast
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for the HTML frontend

forecaster = PassengerForecast()

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """
    Returns 48-period (24-hour) passenger arrival forecast
    Each period = 30 minutes
    """
    forecast_data = forecaster.generate_forecast_30min(48)
    return jsonify({'forecast': forecast_data})

@app.route('/api/forecast/cumulative', methods=['GET'])
def get_cumulative_forecast():
    """
    Returns cumulative passenger count forecast
    """
    cumulative_data = forecaster.get_cumulative_forecast(48)
    return jsonify({'cumulative': cumulative_data})

@app.route('/api/forecast/stats', methods=['GET'])
def get_forecast_stats():
    """
    Returns summary statistics for the 24-hour forecast
    """
    stats = forecaster.get_summary_stats(48)
    return jsonify(stats)

@app.route('/api/forecast/next-6h', methods=['GET'])
def get_next_6h_forecast():
    """
    Returns next 6 hours of forecast (12 periods of 30 minutes each)
    Useful for immediate simulation input
    """
    forecast_data = forecaster.generate_forecast_30min(12)
    return jsonify({'forecast': forecast_data})

@app.route('/api/forecast/live-injection', methods=['GET'])
def get_live_injection():
    """
    Returns the next period's passenger count for live injection into simulation
    """
    forecast = forecaster.generate_forecast_30min(1)
    if forecast:
        return jsonify({
            'next_passengers': forecast[0]['passengers'],
            'time': forecast[0]['time_label']
        })
    return jsonify({'error': 'No forecast data'}), 500

@app.route('/simulation', methods=['GET'])
def simulation():
    """
    Serves the interactive terminal check-in flow simulation
    """
    file_path = os.path.join(os.path.dirname(__file__), 'simulation_view.html')
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'error': 'Simulation file not found'}), 404

if __name__ == '__main__':
    print("Starting Airport Terminal Simulation Forecast API...")
    print("Server running on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET /api/forecast - Full 24h forecast (30-min intervals)")
    print("  GET /api/forecast/cumulative - Cumulative forecast")
    print("  GET /api/forecast/stats - Summary statistics")
    print("  GET /api/forecast/next-6h - Next 6 hours only")
    print("  GET /api/forecast/live-injection - Next period's data")
    print("  GET /simulation - Interactive check-in flow simulation")
    
    app.run(debug=True, port=5000)
