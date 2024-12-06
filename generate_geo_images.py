import math
import os

from exif import Image as ExifImage
from PIL import Image, ImageDraw, ImageFont


def decimal_to_dms(decimal_degree):
    """
    Converts a decimal degree to degrees, minutes, and seconds (DMS).

    Parameters:
        decimal_degree (float): The decimal degree to convert.

    Returns:
        tuple: A tuple containing degrees, minutes, and seconds.
    """
    # Get the sign of the input for direction (e.g., N/S or E/W)
    sign = -1 if decimal_degree < 0 else 1
    decimal_degree = abs(decimal_degree)

    # Extract degrees
    degrees = int(decimal_degree)

    # Extract minutes
    minutes_decimal = (decimal_degree - degrees) * 60
    minutes = int(minutes_decimal)

    # Extract seconds
    seconds = (minutes_decimal - minutes) * 60
    seconds = int(seconds)

    # Apply the original sign to the degrees
    # degrees *= sign

    return tuple(map(float, (degrees, minutes, seconds)))


# Helper function to calculate coordinates for 1 km increments
def generate_coordinates(lat_min, lat_max, lon_min, lon_max, step_km=1):
    # Approximation of 1 degree latitude in kilometers
    km_per_degree = 111
    lat_step = step_km / km_per_degree
    lon_step = step_km / (km_per_degree * math.cos(math.radians(lat_min)))

    coordinates = []
    lat = lat_min
    while lat <= lat_max:
        lon = lon_min
        while lon <= lon_max:
            coordinates.append((lat, lon))
            lon += lon_step
        lat += lat_step
    return coordinates


# Helper function to create an image with geo-information
def create_image(lat, lon, output_dir, image_size=(500, 500)):
    img = Image.new("RGB", image_size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Adding text info to the image
    font_size = 20
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text = f"Lat: {lat:.6f}, Lon: {lon:.6f}"
    draw.text((10, 10), text, fill="black", font=font)

    # Save image
    image_path = os.path.join(output_dir, f"image_{lat:.6f}_{lon:.6f}.jpg")
    img.save(image_path)

    # Add EXIF geo-information
    with open(image_path, "rb") as file:
        exif_img = ExifImage(file)

    exif_img.gps_latitude = decimal_to_dms(lat)
    exif_img.gps_latitude_ref = "N" if lat >= 0 else "S"
    exif_img.gps_longitude = decimal_to_dms(lon)
    exif_img.gps_longitude_ref = "E" if lon >= 0 else "W"

    with open(image_path, "wb") as file:
        file.write(exif_img.get_file())
    print(f"Image created: {image_path}")


# Main function to generate images
def generate_images(lat_min, lat_max, lon_min, lon_max, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    coordinates = generate_coordinates(lat_min, lat_max, lon_min, lon_max, step_km=1)
    print(f"{len(coordinates)} images will be generated.")

    for lat, lon in coordinates:
        create_image(lat, lon, output_dir)


# Specify bounding box and output directory
LAT_MIN = 40.0
LAT_MAX = 40.02
LON_MIN = -74.0
LON_MAX = -73.98
OUTPUT_DIR = "geo_images"

generate_images(LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, OUTPUT_DIR)
