# Geo Converter - Reverse Geocoding Application

A simple Python application for reverse geocoding latitude/longitude coordinates to city names using the OpenStreetMap Nominatim API.

## Features

- 🌍 Reverse geocode coordinates to city names
- 📊 Simple CSV upload interface
- 🚀 Batch processing of multiple coordinates
- 💾 Export results to CSV
- 📈 Progress tracking and statistics
- ✅ Error handling and validation

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [CSV Format](#csv-format)
- [API Information](#api-information)
- [Debugging](#debugging)
- [Common Issues](#common-issues)
- [Technical Details](#technical-details)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd geo_converter
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

1. **Start the Streamlit app**
   ```bash
   streamlit run app.py
   ```

2. **Access the web interface**
   - The application will automatically open in your default browser
   - Default URL: http://localhost:8501

3. **Upload your CSV file**
   - Click on "Upload CSV file with coordinates"
   - Select a CSV file containing latitude and longitude columns

4. **Configure column names** (if needed)
   - Use the sidebar to specify custom column names
   - Default: `latitude` and `longitude`

5. **Start geocoding**
   - Click the "Start Geocoding" button
   - Wait for processing to complete
   - Download the results CSV file

## CSV Format

### Input CSV Requirements

Your CSV file should contain at least two columns for coordinates:

**Example:**
```csv
latitude,longitude
40.7128,-74.0060
51.5074,-0.1278
35.6762,139.6503
```

**Alternative column names:**
```csv
lat,lon
40.7128,-74.0060
51.5074,-0.1278
```

You can specify custom column names in the sidebar configuration.

### Output CSV Columns

The output CSV will include:
- All original columns from your input file
- `city` - City name (or town, village, etc.)
- `state` - State/province name
- `country` - Country name
- `country_code` - ISO country code
- `postcode` - Postal code
- `display_name` - Full formatted address
- `status` - Processing status ('success' or error message)

## API Information

### Nominatim API

This application uses the [OpenStreetMap Nominatim API](https://nominatim.openstreetmap.org/) for reverse geocoding.

**Endpoint:** `https://nominatim.openstreetmap.org/reverse`

**Usage Policy:**
- Maximum 1 request per second
- No heavy usage (this application respects the rate limit)
- Appropriate User-Agent header is set

**API Parameters Used:**
- `lat` - Latitude coordinate
- `lon` - Longitude coordinate
- `format=json` - Response format
- `addressdetails=1` - Include detailed address components

### Example API Response

```json
{
  "address": {
    "city": "New York",
    "state": "New York",
    "country": "United States",
    "country_code": "us",
    "postcode": "10007"
  },
  "display_name": "New York, NY 10007, United States"
}
```

## Debugging

### Debug Mode

To see detailed logs, run the application with verbose logging:

```bash
streamlit run app.py --logger.level=debug
```

### Testing Individual Coordinates

You can test the geocoder module independently:

```python
from geocoder import ReverseGeocoder

# Initialize geocoder
geo = ReverseGeocoder()

# Test a single coordinate
result = geo.reverse_geocode(40.7128, -74.0060)
print(result)
```

### Checking API Response

To debug API responses, you can add print statements in `geocoder.py`:

```python
def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Optional[str]]:
    # ... existing code ...
    response = self.session.get(self.base_url, params=params, timeout=10)
    print(f"API Response: {response.json()}")  # Debug line
    # ... rest of code ...
```

## Common Issues

### Issue 1: Column Names Not Found

**Error:** `Columns 'latitude' and/or 'longitude' not found in CSV file!`

**Solution:**
- Check your CSV file column names
- Update the column names in the sidebar configuration
- Ensure column names match exactly (case-sensitive)

### Issue 2: Slow Processing

**Cause:** Nominatim API rate limit (1 request per second)

**Solution:**
- This is expected behavior to respect the API usage policy
- For 100 coordinates, expect ~100 seconds processing time
- Consider breaking large files into smaller batches

### Issue 3: Some Coordinates Return No City

**Cause:**
- Coordinates in remote areas (ocean, desert, etc.)
- Very precise coordinates that don't map to a city

**Solution:**
- Check the `display_name` field for general location info
- Verify coordinates are correct
- Some locations may only have state/country information

### Issue 4: Network Errors

**Error:** `error: HTTPSConnectionPool...`

**Solution:**
- Check your internet connection
- Verify the Nominatim API is accessible
- Check if there's a firewall blocking the request

### Issue 5: Rate Limiting or Blocking

**Error:** `HTTP 429 Too Many Requests` or `HTTP 403 Forbidden`

**Cause:** Too many requests or blocked by API

**Solution:**
- The app already implements 1 request/second delay
- Ensure you're not running multiple instances
- Wait a few minutes before trying again
- Consider using a different API endpoint if available

## Technical Details

### Project Structure

```
geo_converter/
├── app.py              # Streamlit UI application
├── geocoder.py         # Reverse geocoding logic
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Main Components

#### 1. ReverseGeocoder Class (`geocoder.py`)

Handles all geocoding operations:
- `reverse_geocode()` - Geocode a single coordinate pair
- `process_csv()` - Batch process CSV files
- `_extract_city()` - Extract city name from API response

#### 2. Streamlit UI (`app.py`)

Provides the user interface:
- File upload functionality
- Configuration options
- Progress tracking
- Results display and download

### Performance Considerations

- **Rate Limiting:** 1 second delay between requests (API requirement)
- **Processing Time:** ~1 second per coordinate
- **Memory Usage:** Loads entire CSV into memory
- **Recommended File Size:** < 1000 rows for reasonable processing time

### Extending the Application

#### Add More Location Fields

Edit `geocoder.py` to include additional fields:

```python
result = {
    'latitude': lat,
    'longitude': lon,
    'city': self._extract_city(address),
    'state': address.get('state'),
    'county': address.get('county'),  # Add county
    'suburb': address.get('suburb'),  # Add suburb
    # ... rest of fields
}
```

#### Use Different Geocoding Services

Replace the Nominatim API with another service:
- Modify `base_url` in `ReverseGeocoder.__init__()`
- Update request parameters in `reverse_geocode()`
- Adjust response parsing logic

#### Add Caching

Implement caching to avoid re-geocoding the same coordinates:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def reverse_geocode(self, lat: float, lon: float):
    # ... existing code ...
```

## License

This project uses the OpenStreetMap Nominatim API, which requires attribution to OpenStreetMap contributors.

## Support

For issues or questions:
1. Check the [Common Issues](#common-issues) section
2. Review the [Debugging](#debugging) guide
3. Check Nominatim API status: https://status.openstreetmap.org/

## Version History

- **v1.0.0** (2025-11-26)
  - Initial release
  - Basic reverse geocoding functionality
  - Streamlit UI
  - CSV batch processing
