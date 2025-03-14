import requests
import json
from datetime import datetime, timedelta
import math
import os
import matplotlib.pyplot as plt
import cv2

class TripPlannerService:
    def __init__(self):
        # Constants for compliance with regulations
        self.MAX_DAILY_DRIVING = 11  # Max driving hours per day
        self.MAX_DAILY_DUTY = 14     # Max on-duty hours per day
        self.MIN_REST_PERIOD = 10    # Min consecutive rest hours per day
        self.MAX_CYCLE_HOURS = 70    # Max duty hours in 8-day cycle
        self.FUEL_DISTANCE = 1000    # Miles between fuel stops
        self.PICKUP_DROPOFF_TIME = 1  # Hour for pickup/dropoff
        self.AVG_SPEED = 55          # Average speed in miles/hour
        
        # OpenRouteService API key and endpoint
        self.ORS_API_KEY = '5b3ce3597851110001cf6248de17e0ce4e6a47d980377adb0d23441b'
        self.ORS_ENDPOINT = 'https://api.openrouteservice.org/v2/directions/driving-hgv'
    
    def _get_coordinates(self, location):
        """Convert address to coordinates using OpenRouteService geocoding API"""
        geocode_url = 'https://api.openrouteservice.org/geocode/search'
        response = requests.get(
            geocode_url,
            params={
                'api_key': self.ORS_API_KEY,
                'text': location,
                'size': 1
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to geocode address: {response.text}")
        
        result = response.json()
        if 'features' in result and len(result['features']) > 0:
            coordinates = result['features'][0]['geometry']['coordinates']
            return coordinates
        else:
            raise Exception(f"No coordinates found for location: {location}")
    
    def calculate_route(self, current_location, pickup_location, dropoff_location):
        """Calculate route using OpenRouteService API"""
        # Get coordinates for locations
        current_coords = self._get_coordinates(current_location)
        pickup_coords = self._get_coordinates(pickup_location)
        dropoff_coords = self._get_coordinates(dropoff_location)
        
        # Build coordinates list for the API request
        # First leg: Current to Pickup
        # Second leg: Pickup to Dropoff
        coordinates = [current_coords, pickup_coords, dropoff_coords]
        
        # Make API request to get the route
        payload = {
            "coordinates": coordinates,
            "instructions": True,         # Include turn-by-turn directions
            "instructions_format": "text",
            "preference": "recommended",  # Recommended route
            "geometry": True,             # Include geometry in response
            "elevation": False,           # No elevation data
            "units": "m"                  # Meters
        }

        headers = {
            "Authorization": self.ORS_API_KEY,  # API Key in Authorization Header
            "Content-Type": "application/json"
        }

        response = requests.post(self.ORS_ENDPOINT, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to calculate route: {response.text}")
        
        route_data = response.json()
        
        # Extract distance and duration from the route data
        total_distance_meters = 0
        total_duration_seconds = 0
        
        for route in route_data.get('routes', []):
            total_distance_meters += route.get('summary', {}).get('distance', 0)
            total_duration_seconds += route.get('summary', {}).get('duration', 0)

        # Convert to miles and hours
        total_distance_miles = total_distance_meters / 1609.34
        total_duration_hours = total_duration_seconds / 3600
        
        # Add time for pickup and dropoff
        total_duration_hours += (2 * self.PICKUP_DROPOFF_TIME)  # 1 hour each for pickup and dropoff
        
        return {
            'route_data': route_data,
            'distance_miles': total_distance_miles,
            'duration_hours': total_duration_hours
        }
        
    def get_stop_coordinates(self, query, lon=None, lat=None):
        """
        Get coordinates of a fuel stop or rest stop using ORS API.
        - query: "fuel stop" or "rest stop"
        - lon, lat: Optional coordinates for better accuracy
        """
        url = f"https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key": self.ORS_API_KEY,
            "text": query,
            "size": 1  # Get the top result
        }
        if lon and lat:
            params["focus.point.lon"] = lon
            params["focus.point.lat"] = lat  # Improve accuracy
        
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("features"):
            location = data["features"][0]["geometry"]["coordinates"]
            return {"longitude": location[0], "latitude": location[1]}
        return None
    
    def plan_rest_stops(self, route_data, current_cycle_used):
        """Plan rest stops based on route data and HOS regulations"""
        total_miles = route_data['distance_miles']
        total_hours = route_data['duration_hours']
        
        # Initialize planning variables
        remaining_daily_driving = self.MAX_DAILY_DRIVING
        remaining_daily_duty = self.MAX_DAILY_DUTY
        remaining_cycle_hours = self.MAX_CYCLE_HOURS - current_cycle_used
        miles_since_last_fuel = 0
        
        # Calculate initial departure time
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        current_time = start_time
        
        # List to store rest stops
        rest_stops = []
        
        # Track journey status
        miles_traveled = 0
        hours_driven = 0
        
        # Split journey into segments
        while miles_traveled < total_miles:
            # Calculate how many miles can be driven before HOS limits
            drivable_hours = min(remaining_daily_driving, remaining_daily_duty, remaining_cycle_hours)
            drivable_miles = drivable_hours * self.AVG_SPEED
            
            # Check if we need a fuel stop
            if miles_since_last_fuel + drivable_miles > self.FUEL_DISTANCE:
                # Calculate where the fuel stop will be
                miles_to_fuel = self.FUEL_DISTANCE - miles_since_last_fuel
                hours_to_fuel = miles_to_fuel / self.AVG_SPEED
                
                # Update trackers
                miles_traveled += miles_to_fuel
                hours_driven += hours_to_fuel
                miles_since_last_fuel = 0
                
                remaining_daily_driving -= hours_to_fuel
                remaining_daily_duty -= hours_to_fuel
                remaining_cycle_hours -= hours_to_fuel
                
                # Add a short rest/fuel stop (30 min)
                fuel_stop_arrival = current_time + timedelta(hours=hours_to_fuel)
                fuel_stop_departure = fuel_stop_arrival + timedelta(minutes=30)
                
                # Calculate location of fuel stop (approximate based on distance)
                fuel_stop_percent = miles_traveled / total_miles
                # In a real app, you'd use the route's waypoints to find the actual location
                fuel_stop_coords = self.get_stop_coordinates("fuel stop")
                fuel_stop_location = fuel_stop_coords if fuel_stop_coords else "Unknown fuel stop"
                
                rest_stops.append({
                    'location': fuel_stop_location,
                    'arrival_time': fuel_stop_arrival,
                    'departure_time': fuel_stop_departure,
                    'rest_duration': 0.5,  # 30 minutes
                    'is_fuel_stop': True
                })
                
                # Update current time
                current_time = fuel_stop_departure
                
                # Subtract rest time from daily duty
                remaining_daily_duty -= 0.5
                
            else:
                # Check if we can complete the remainder of the journey
                remaining_miles = total_miles - miles_traveled
                hours_needed = remaining_miles / self.AVG_SPEED
                
                if hours_needed <= drivable_hours:
                    # We can complete the journey without another rest
                    miles_traveled = total_miles
                    hours_driven += hours_needed
                    current_time += timedelta(hours=hours_needed)
                else:
                    # Drive as far as allowed by HOS, then take required rest
                    miles_traveled += drivable_miles
                    hours_driven += drivable_hours
                    miles_since_last_fuel += drivable_miles
                    
                    # Update time
                    current_time += timedelta(hours=drivable_hours)
                    
                    # Calculate rest duration
                    rest_hours = self.MIN_REST_PERIOD
                    
                    # Add rest stop
                    rest_stop_arrival = current_time
                    rest_stop_departure = rest_stop_arrival + timedelta(hours=rest_hours)
                    
                    # Calculate location of rest stop (approximate based on distance)
                    rest_stop_percent = miles_traveled / total_miles
                    rest_stop_coords = self.get_stop_coordinates("rest stop")
                    rest_stop_location = rest_stop_coords if rest_stop_coords else "Unknown rest stop"
                    
                    rest_stops.append({
                        'location': rest_stop_location,
                        'arrival_time': rest_stop_arrival,
                        'departure_time': rest_stop_departure,
                        'rest_duration': rest_hours,
                        'is_fuel_stop': False
                    })
                    
                    # Reset daily limits after rest
                    remaining_daily_driving = self.MAX_DAILY_DRIVING
                    remaining_daily_duty = self.MAX_DAILY_DUTY
                    
                    # Update current time
                    current_time = rest_stop_departure
        
        # Return journey stats and rest stops
        return {
            'total_miles': total_miles,
            'total_driving_hours': hours_driven,
            'departure_time': start_time,
            'estimated_arrival': current_time,
            'rest_stops': rest_stops
        }
    
    def generate_eld_logs(self, trip_plan_data, rest_stops_data):
        """
        Generate a structured ELD log ensuring that each day totals 24 hours.
        Includes on-duty, off-duty, driving, and rest periods.
        """
        departure_time = rest_stops_data['departure_time']
        arrival_time = rest_stops_data['estimated_arrival']
        rest_stops = rest_stops_data['rest_stops']

        current_day = departure_time.date()
        end_day = arrival_time.date()
        eld_logs = []

        while current_day <= end_day:
            day_log = {
                'date': current_day,
                'log_entries': [],
                'total_driving_hours': 0,
                'total_on_duty_hours': 0,
                'total_miles': 0
            }

            # Set start and end times for the current day
            day_start = max(departure_time, datetime.combine(current_day, datetime.min.time()))
            day_end = min(arrival_time, datetime.combine(current_day + timedelta(days=1), datetime.min.time()))
            current_time = day_start

            # Start with on-duty pre-trip inspection (30 min)
            day_log['log_entries'].append({
                'status': 'on_duty',
                'start_hour': current_time.hour + current_time.minute / 60.0,
                'end_hour': (current_time + timedelta(minutes=30)).hour + (current_time + timedelta(minutes=30)).minute / 60.0
            })
            current_time += timedelta(minutes=30)
            day_log['total_on_duty_hours'] += 0.5

            # Process rest stops for the day
            day_rest_stops = [stop for stop in rest_stops if stop['arrival_time'].date() == current_day]

            for stop in day_rest_stops:
                if current_time < stop['arrival_time']:
                    self._add_driving_entry(day_log, current_time, stop['arrival_time'])
                self._add_rest_entry(day_log, stop)
                current_time = stop['departure_time']

            # Fill remaining driving time before reaching the end of the day
            if current_time < day_end:
                self._add_driving_entry(day_log, current_time, day_end)

            # Ensure the day ends with 24 hours by filling remaining time as off-duty
            last_entry = day_log['log_entries'][-1]
            if last_entry['end_hour'] < 24:
                day_log['log_entries'].append({
                    'status': 'off_duty',
                    'start_hour': last_entry['end_hour'],
                    'end_hour': 24
                })
            
            # Compute total miles driven
            day_log['total_miles'] = day_log['total_driving_hours'] * 55  # Assuming 55 mph average

            eld_logs.append(day_log)
            current_day += timedelta(days=1)

        return eld_logs

    def _add_driving_entry(self, day_log, start_time, end_time):
        """ Helper to add driving entries ensuring compliance with daily limits """
        start_hour = start_time.hour + start_time.minute / 60.0
        end_hour = end_time.hour + end_time.minute / 60.0

        if end_hour > start_hour:
            day_log['log_entries'].append({
                'status': 'driving',
                'start_hour': start_hour,
                'end_hour': end_hour
            })
            day_log['total_driving_hours'] += end_hour - start_hour
            day_log['total_on_duty_hours'] += end_hour - start_hour

    def _add_rest_entry(self, day_log, stop):
        """ Helper to add rest entries correctly handling fuel stops and sleep breaks """
        rest_start_hour = stop['arrival_time'].hour + stop['arrival_time'].minute / 60.0
        rest_end_hour = stop['departure_time'].hour + stop['departure_time'].minute / 60.0

        if stop['is_fuel_stop']:
            day_log['log_entries'].append({
                'status': 'on_duty',
                'start_hour': rest_start_hour,
                'end_hour': min(rest_start_hour + 0.5, rest_end_hour)
            })
            day_log['total_on_duty_hours'] += min(0.5, rest_end_hour - rest_start_hour)

            if rest_end_hour > rest_start_hour + 0.5:
                day_log['log_entries'].append({
                    'status': 'off_duty',
                    'start_hour': rest_start_hour + 0.5,
                    'end_hour': rest_end_hour
                })
        else:
            day_log['log_entries'].append({
                'status': 'off_duty',
                'start_hour': rest_start_hour,
                'end_hour': rest_end_hour
            })
    
    def draw_eld_lines(hours):
        # Load the image
        image_path = os.path.abspath("blank-paper-log.png")
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Define the log graph area coordinates
        height, width, _ = img.shape
        graph_top = int(height * 0.37)
        graph_bottom = int(height * 0.47)
        graph_left = int(width * 0.12)
        graph_right = int(width * 0.9)
        hour_step = (graph_right - graph_left) / 24
        
        # Define duty status levels (approximate pixel positions)
        status_levels = {
            'off_duty': graph_top,
            'sleeper': graph_top + (graph_bottom - graph_top) * 0.35,
            'driving': graph_top + (graph_bottom - graph_top) * 0.65,
            'on_duty': graph_bottom
        }
        
        # Create a figure
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(img)
        
        # Draw ELD lines
        prev_x, prev_y = None, None
        for i, (hour, status) in enumerate(hours):
            x = graph_left + hour * hour_step
            y = status_levels[status]
            
            if prev_x is not None and prev_y is not None:
                ax.scatter([x, x], [prev_y, y], color='red', zorder=2)
                ax.scatter(prev_x, prev_y, color='red', s=40, zorder=2)
                ax.scatter(x, y, color='red', s=40, zorder=2)
                ax.plot([x, x], [prev_y, y], color='black', linewidth=2, zorder=1)
                ax.plot([prev_x, x], [prev_y, prev_y], color='black', linewidth=2, zorder=1)
            
            prev_x, prev_y = x, y
        
        # Ensure the last point extends to the end
        last_x = graph_right
        ax.plot([prev_x, last_x], [prev_y, prev_y], color='black', linewidth=2, zorder=1)
        ax.scatter(last_x, prev_y, color='red', s=40, zorder=2)
        
        # Display the overlayed image
        plt.axis('off')
        plt.show()