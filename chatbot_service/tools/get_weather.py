def get_weather(location: str) -> str:
    """
    Get the current weather information for a specific location.
    Use this function when you need accurate, real-time weather data for any location.
    
    Args:
        location (str): The city, region, or address to get weather for (e.g., "New York", "London", "Tokyo")
        
    Returns:
        str: Detailed weather information including temperature, conditions, and forecast.
    """
    # In a real implementation, this would call a weather API
    weather_info = {
        "Ho Chi Minh City": "32°C, Sunny with occasional clouds. Humidity: 75%. Feels like 35°C.",
        "New York": "18°C, Partly cloudy. Humidity: 45%. Chance of rain: 20%.",
        "London": "14°C, Light rain. Humidity: 80%. Wind: 15 km/h.",
        "Tokyo": "25°C, Clear skies. Humidity: 60%. UV index: High."
    }
    
    # Fallback response for locations not in our mock database
    if location not in weather_info:
        return f"22°C, Partly cloudy in {location}. Humidity: 60%."
        
    return {"weather_info": weather_info[location] }

    
def get_current_location() -> str:
    """
    Get the user's current location based on their device or connection information.
    Use this function when location information is needed but not explicitly provided by the user.
    This is particularly useful for queries about local information, weather, or services "near me" or "here".
    
    Returns:
        str: The user's current city or region name.
    """
    # In a real implementation, this would detect the user's location
    # For demo purposes, we'll return a fixed location
    return { "location": "Ho Chi Minh City" }