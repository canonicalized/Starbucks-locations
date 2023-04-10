import openrouteservice as ors

# Replace with your own API key
api_key = "5b3ce3597851110001cf62487b53781d84d24a52a72ed5e13d79c11e"

# Create a client using your API key
client = ors.Client(key=api_key)

# Define the start and end locations as longitude/latitude pairs
start_location = [-122.4194, 37.7749]
end_location = [-122.4085, 37.8018]

# Calculate the route between the start and end locations
route = client.directions(
    coordinates=[start_location, end_location],
    profile='foot-walking',
)
print(route)
# Print the distance and travel time for the route
distance = route['routes'][0]['distance'] / 1000  # convert to kilometers
duration = route['routes'][0]['duration'] / 60  # convert to minutes
print(f"Distance: {distance:.2f} km")
print(f"Duration: {duration:.2f} minutes")