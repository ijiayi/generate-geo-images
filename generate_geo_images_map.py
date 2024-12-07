import argparse
import math
import os

from exif import Image as ExifImage
from PIL import Image, ImageDraw, ImageFont
from staticmap import CircleMarker, StaticMap


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


def create_static_map(coordinates, filename, zoom_level=10, image_size=(500, 500)):
    coordinates = (coordinates[1], coordinates[0])

    m = StaticMap(*image_size, url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')

    marker_outline = CircleMarker(coordinates, 'white', 18)
    marker = CircleMarker(coordinates, '#ff0000', 12)

    m.add_marker(marker_outline)
    m.add_marker(marker)

    image = m.render(zoom_level)
    image.save(filename)


# Helper function to create an image with geo-information
def create_image(lat, lon, output_dir, image_size=(500, 500), zoom_level=10):

    image_path = os.path.join(output_dir, f"image_{lat:.6f}_{lon:.6f}.jpg")

    create_static_map((lat, lon), image_path, image_size=image_size, zoom_level=zoom_level)

    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Adding text info to the image
    font_size = 24
    try:
        font = ImageFont.truetype("SF-Mono-Regular.otf", font_size)
    except IOError:
        font = ImageFont.load_default()

    text = f"Lat, Lon: {lat:.6f}, {lon:.6f}\nZoom: {zoom_level}"
    draw.text((10, 10), text, fill="black", font=font, stroke_width=2, stroke_fill="white")

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
def generate_images(
    lat_min, lat_max, lon_min, lon_max, output_dir, step_km=1, zoom_level=12, image_size=(500, 500)
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    coordinates = generate_coordinates(lat_min, lat_max, lon_min, lon_max, step_km=step_km)
    print(f"{len(coordinates)} images will be generated.")

    for lat, lon in coordinates:
        create_image(lat, lon, output_dir, image_size=image_size, zoom_level=zoom_level)


# # Specify bounding box and output directory
# LAT_MIN = 40.0
# LAT_MAX = 40.02
# LON_MIN = -74.0
# LON_MAX = -73.98
# OUTPUT_DIR = "geo_images"

# # Specify bounding box and output directory
# LAT_MIN = 21.9
# LAT_MAX = 25.3
# LON_MIN = 119.5
# LON_MAX = 122.0
# OUTPUT_DIR = "geo_images"

# generate_images(
#     LAT_MIN,
#     LAT_MAX,
#     LON_MIN,
#     LON_MAX,
#     OUTPUT_DIR,
#     step_km=10,
#     zoom_level=12,
#     image_size=(800, 800),
# )


def main():
    parser = argparse.ArgumentParser(
        description="Generate geo images within a bounding box.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-b",
        "--bounding-box",
        type=str,
        default="40.0,40.02,-74.0,-73.98",
        help="Bounding box as lat_min,lat_max,lon_min,lon_max",
    )
    parser.add_argument(
        "-o", "--output-dir", type=str, default="geo_images", help="Output directory"
    )
    parser.add_argument("-s", "--step-km", type=int, default=1, help="Step size in kilometers")
    parser.add_argument(
        "-z", "--zoom-level", type=int, default=12, help="Zoom level for the images"
    )
    parser.add_argument(
        "-i",
        "--image-size",
        type=int,
        nargs=2,
        default=(500, 500),
        help="Image size as width and height",
    )

    args = parser.parse_args()

    lat_min, lat_max, lon_min, lon_max = map(float, args.bounding_box.split(','))

    generate_images(
        lat_min,
        lat_max,
        lon_min,
        lon_max,
        args.output_dir,
        step_km=args.step_km,
        zoom_level=args.zoom_level,
        image_size=tuple(args.image_size),
    )


if __name__ == "__main__":
    main()
