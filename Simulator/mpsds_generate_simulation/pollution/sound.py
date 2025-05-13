import random
import numpy as np
import matplotlib.pyplot as plt

class HouseSoundSimulation:
    def __init__(self, rooms=['living_room', 'kitchen', 'bedroom', 'home_office']):
        """
        Initialize a time-dependent house sound simulation
        
        Sound Level Categories:
        - Soft sounds: 20-50 dB (whispers, quiet activities)
        - Moderate sounds: 50-70 dB (normal conversation, typical household noise)
        """
        self.rooms = rooms
        
        # Sound level ranges (in decibels)
        self.sound_levels = {
            'soft': (20, 50),
            'moderate': (50, 70)
        }
        
        # Time-dependent activity probabilities
        self.activity_schedule = {
            'living_room': {
                '00:00-06:00': {'active_prob': 0.05, 'sound_type': 'soft'},    # Late night
                '06:00-08:00': {'active_prob': 0.3, 'sound_type': 'moderate'}, # Morning preparation
                '08:00-12:00': {'active_prob': 0.2, 'sound_type': 'soft'},     # Work/study time
                '12:00-14:00': {'active_prob': 0.4, 'sound_type': 'moderate'}, # Lunch time
                '14:00-18:00': {'active_prob': 0.3, 'sound_type': 'soft'},     # Afternoon activities
                '18:00-22:00': {'active_prob': 0.7, 'sound_type': 'moderate'}, # Evening peak
                '22:00-24:00': {'active_prob': 0.2, 'sound_type': 'soft'}      # Wind down
            },
            'kitchen': {
                '00:00-06:00': {'active_prob': 0.05, 'sound_type': 'soft'},    # Rare midnight snack
                '06:00-08:00': {'active_prob': 0.6, 'sound_type': 'moderate'}, # Breakfast
                '08:00-12:00': {'active_prob': 0.1, 'sound_type': 'soft'},     # Quiet time
                '12:00-14:00': {'active_prob': 0.7, 'sound_type': 'moderate'}, # Lunch preparation
                '14:00-18:00': {'active_prob': 0.2, 'sound_type': 'soft'},     # Occasional snack
                '18:00-22:00': {'active_prob': 0.8, 'sound_type': 'moderate'}, # Dinner preparation
                '22:00-24:00': {'active_prob': 0.1, 'sound_type': 'soft'}      # Clean up, wind down
            },
            'bedroom': {
                '00:00-06:00': {'active_prob': 0.1, 'sound_type': 'soft'},     # Sleep, occasional movement
                '06:00-08:00': {'active_prob': 0.3, 'sound_type': 'soft'},     # Waking up
                '08:00-12:00': {'active_prob': 0.1, 'sound_type': 'soft'},     # Potentially empty
                '12:00-14:00': {'active_prob': 0.2, 'sound_type': 'soft'},     # Occasional rest
                '14:00-18:00': {'active_prob': 0.2, 'sound_type': 'soft'},     # Reading, relaxing
                '18:00-22:00': {'active_prob': 0.3, 'sound_type': 'soft'},     # Winding down
                '22:00-24:00': {'active_prob': 0.4, 'sound_type': 'soft'}      # Preparing for sleep
            },
            'home_office': {
                '00:00-06:00': {'active_prob': 0.01, 'sound_type': 'soft'},    # Almost never
                '06:00-08:00': {'active_prob': 0.2, 'sound_type': 'soft'},     # Early work prep
                '08:00-12:00': {'active_prob': 0.6, 'sound_type': 'moderate'}, # Work hours
                '12:00-14:00': {'active_prob': 0.4, 'sound_type': 'soft'},     # Lunch break
                '14:00-18:00': {'active_prob': 0.5, 'sound_type': 'moderate'}, # Afternoon work
                '18:00-22:00': {'active_prob': 0.3, 'sound_type': 'soft'},     # Evening wrap-up
                '22:00-24:00': {'active_prob': 0.1, 'sound_type': 'soft'}      # Late night work
            }
        }
        
        # Store simulation results
        self.simulation_data = {}
    
    def _get_time_period(self, hour):
        """
        Convert hour to time period string
        
        :param hour: Hour of the day (0-23)
        :return: Time period string
        """
        hour = int(hour)
        return f"{hour:02d}:00-{(hour+1)%24:02d}:00"
    
    def generate_sound_level(self, sound_type='soft'):
        """
        Generate a random sound level within the specified range
        
        :param sound_type: Type of sound ('soft' or 'moderate')
        :return: Random sound level in decibels
        """
        min_level, max_level = self.sound_levels[sound_type]
        return random.uniform(min_level, max_level)
    
    def simulate_room_sounds(self, duration_hours=24):
        """
        Simulate sound levels in each room over a specified duration
        
        :param duration_hours: Simulation duration in hours
        :return: Dictionary of sound level data for each room
        """
        for room in self.rooms:
            # Generate time series of sound levels
            time_points = np.linspace(0, duration_hours, num=50)
            sound_levels = []
            
            for time in time_points:
                # Get current hour and corresponding time period
                hour = time % 24
                time_period = self._get_time_period(hour)
                
                # Get activity parameters for this room and time
                room_schedule = self.activity_schedule[room].get(time_period, 
                    {'active_prob': 0.1, 'sound_type': 'soft'})
                
                # Determine if room is active based on probability
                if random.random() < room_schedule['active_prob']:
                    sound_levels.append(
                        self.generate_sound_level(room_schedule['sound_type'])
                    )
                else:
                    # Minimal background noise when inactive
                    sound_levels.append(random.uniform(10, 20))
            
            self.simulation_data[room] = {
                'time': time_points,
                'sound_levels': sound_levels
            }
        
        return self.simulation_data
    
    def visualize_sound_levels(self):
        """
        Create a visualization of sound levels across rooms
        """
        plt.figure(figsize=(12, 6))
        
        for room, data in self.simulation_data.items():
            plt.plot(data['time'], data['sound_levels'], label=room)
        
        plt.title('Sound Levels Across House Rooms')
        plt.xlabel('Time (hours)')
        plt.ylabel('Sound Level (dB)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()
    
    def analyze_sound_exposure(self):
        """
        Analyze sound exposure statistics for each room
        
        :return: Dictionary with sound exposure statistics
        """
        sound_stats = {}
        
        for room, data in self.simulation_data.items():
            sound_levels = data['sound_levels']
            sound_stats[room] = {
                'average_sound_level': np.mean(sound_levels),
                'max_sound_level': np.max(sound_levels),
                'min_sound_level': np.min(sound_levels),
                'sound_level_variance': np.var(sound_levels)
            }
        
        return sound_stats

# Example usage
def main():
    # Create a house sound simulation
    house_sim = HouseSoundSimulation()
    
    # Run simulation
    simulation_results = house_sim.simulate_room_sounds(duration_hours=24)
    
    # Visualize sound levels
    house_sim.visualize_sound_levels()
    
    # Analyze sound exposure
    sound_exposure = house_sim.analyze_sound_exposure()
    
    # Print sound exposure statistics
    print("Sound Exposure Statistics:")
    for room, stats in sound_exposure.items():
        print(f"\n{room.replace('_', ' ').title()}:")
        for stat, value in stats.items():
            print(f"  {stat.replace('_', ' ').title()}: {value:.2f}")

if __name__ == "__main__":
    main()