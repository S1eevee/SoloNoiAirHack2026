import math
from datetime import datetime, timedelta
import json

class PassengerForecast:
    """
    Generates realistic passenger arrival forecasts for airport terminals.
    Based on typical airport traffic patterns and seasonal variations.
    """
    
    def __init__(self):
        self.base_hourly_rate = 150  # Base passengers per hour
        self.peak_hours = [7, 8, 9, 17, 18, 19]  # Morning and evening peaks
        self.low_hours = [2, 3, 4, 5]  # Night-time low traffic
        
    def get_hourly_pattern(self, hour):
        """
        Returns a multiplier for the given hour of day (0-23)
        based on typical airport traffic patterns.
        """
        if hour in self.peak_hours:
            return 1.8  # 80% increase during peak hours
        elif hour in self.low_hours:
            return 0.3  # 70% decrease during night
        elif hour in [12, 13]:  # Lunch time
            return 1.3
        elif hour in [20, 21, 22]:  # Evening decrease
            return 1.1
        else:
            return 1.0  # Normal hours
    
    def get_day_pattern(self, day_of_week):
        """
        Returns a multiplier for the given day of week (0=Monday, 6=Sunday)
        """
        if day_of_week >= 5:  # Weekend
            return 0.85
        elif day_of_week == 0:  # Monday
            return 1.2  # Higher Monday traffic
        else:
            return 1.0
    
    def generate_forecast_30min(self, num_periods=48):
        """
        Generates passenger arrival forecast for the next 30-minute intervals.
        num_periods: number of 30-minute periods to forecast (default: 48 = 24 hours)
        
        Returns: List of dicts with timestamp and predicted passenger count
        """
        forecast = []
        now = datetime.now()
        day_of_week = now.weekday()
        
        for i in range(num_periods):
            # Calculate time for this period
            forecast_time = now + timedelta(minutes=30 * i)
            hour = forecast_time.hour
            
            # Base calculation
            base_30min = (self.base_hourly_rate / 2)  # 30 min = half hour
            
            # Apply hour-of-day pattern
            hour_multiplier = self.get_hourly_pattern(hour)
            
            # Apply day-of-week pattern
            day_multiplier = self.get_day_pattern(day_of_week)
            
            # Add some realistic variance (±10%)
            variance = 1 + (math.sin(i * 0.5) * 0.1)
            
            # Calculate predicted passengers for this 30-minute interval
            predicted = int(base_30min * hour_multiplier * day_multiplier * variance)
            predicted = max(10, predicted)  # Minimum 10 passengers per interval
            
            forecast.append({
                'timestamp': forecast_time.isoformat(),
                'time_label': forecast_time.strftime('%H:%M'),
                'passengers': predicted,
                'period': i
            })
        
        return forecast
    
    def get_cumulative_forecast(self, num_periods=48):
        """
        Returns cumulative passenger count forecast.
        Useful for capacity planning.
        """
        forecast = self.generate_forecast_30min(num_periods)
        cumulative = 0
        cumulative_data = []
        
        for point in forecast:
            cumulative += point['passengers']
            cumulative_data.append({
                'timestamp': point['timestamp'],
                'time_label': point['time_label'],
                'cumulative': cumulative,
                'period': point['period']
            })
        
        return cumulative_data
    
    def get_summary_stats(self, num_periods=48):
        """
        Returns summary statistics for the forecast period.
        """
        forecast = self.generate_forecast_30min(num_periods)
        passengers_list = [p['passengers'] for p in forecast]
        
        return {
            'total_forecast': sum(passengers_list),
            'average_per_interval': int(sum(passengers_list) / len(passengers_list)),
            'peak_interval': max(passengers_list),
            'low_interval': min(passengers_list),
            'num_periods': len(passengers_list)
        }


def generate_forecast_json(num_periods=48):
    """
    Helper function to generate and return forecast data as JSON.
    """
    forecaster = PassengerForecast()
    
    return {
        'forecast': forecaster.generate_forecast_30min(num_periods),
        'cumulative': forecaster.get_cumulative_forecast(num_periods),
        'stats': forecaster.get_summary_stats(num_periods)
    }


if __name__ == "__main__":
    # Test the forecast generator
    forecaster = PassengerForecast()
    
    print("=== 24-Hour Passenger Forecast (30-min intervals) ===\n")
    forecast = forecaster.generate_forecast_30min(48)
    
    for i, period in enumerate(forecast[:10]):  # Show first 10 periods
        print(f"{period['time_label']}: {period['passengers']} passengers")
    
    print("\n... [showing first 10 of 48 periods] ...\n")
    
    stats = forecaster.get_summary_stats(48)
    print(f"Total Forecast (24h): {stats['total_forecast']} passengers")
    print(f"Average per 30-min: {stats['average_per_interval']} passengers")
    print(f"Peak 30-min period: {stats['peak_interval']} passengers")
    print(f"Low 30-min period: {stats['low_interval']} passengers")
