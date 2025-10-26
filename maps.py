import folium
from geopy.geocoders import Nominatim

def create_map(addresses, output_file="addresses_map.html"):
    """Create a map with given addresses and save as HTML."""
    geolocator = Nominatim(user_agent="map_app", timeout=10)
    m = folium.Map(location=[37.7749, -122.4194], zoom_start=5)

    for address in addresses:
        try:
            location = geolocator.geocode(address)
            if location:
                folium.Marker(
                    [location.latitude, location.longitude],
                    popup=address
                ).add_to(m)
                print(f"✅ Added: {address}")
            else:
                print(f"⚠️ Not found: {address}")
        except Exception as e:
            print(f"❌ Error geocoding {address}: {e}")

    m.save(output_file)
    print(f"📍 Map saved as '{output_file}'")
    return output_file

# Example usage:
if __name__ == "__main__":
    addresses = [
        "5120 SE Powell Blvd",
        "1 Apple Park Way, Cupertino, CA",
        "111 8th Avenue, New York, NY"
    ]

    # Step 1: Create map
    html_path = create_map(addresses)
