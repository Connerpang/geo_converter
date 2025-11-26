import requests
import time
import pandas as pd
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode


class ReverseGeocoder:
    """
    A class to handle reverse geocoding using OpenStreetMap Nominatim API.
    Includes caching and retry logic for improved performance and reliability.
    """

    def __init__(self, base_url: str = "https://nominatim.openstreetmap.org/reverse"):
        """
        Initialize the ReverseGeocoder.

        Args:
            base_url: The base URL for the Nominatim reverse geocoding API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoConverter/1.0 (Reverse Geocoding App)'
        })
        self.cache = {}  # Cache for storing geocoded results
        self.cache_hits = 0
        self.cache_misses = 0

    def reverse_geocode(self, lat: float, lon: float, max_retries: int = 3) -> Dict[str, Optional[str]]:
        """
        Reverse geocode a single coordinate pair to get location information.
        Uses caching to avoid duplicate API calls and retry logic for reliability.

        Args:
            lat: Latitude
            lon: Longitude
            max_retries: Maximum number of retry attempts for failed requests

        Returns:
            Dictionary containing location information
        """
        # Round coordinates to 4 decimal places for cache key (~11m precision)
        cache_key = (round(lat, 4), round(lon, 4))

        # Check cache first
        if cache_key in self.cache:
            self.cache_hits += 1
            cached_result = self.cache[cache_key].copy()
            cached_result['latitude'] = lat
            cached_result['longitude'] = lon
            return cached_result

        self.cache_misses += 1

        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'accept-language': 'en'
        }

        last_error = None

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Respect Nominatim's usage policy (max 1 request per second)
                time.sleep(1)

                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                # Extract address components
                address = data.get('address', {})

                result = {
                    'latitude': lat,
                    'longitude': lon,
                    'city': self._extract_city(address),
                    'state': address.get('state'),
                    'country': address.get('country'),
                    'country_code': address.get('country_code', '').upper(),
                    'postcode': address.get('postcode'),
                    'display_name': data.get('display_name'),
                    'status': 'success'
                }

                # Store in cache
                self.cache[cache_key] = result.copy()

                return result

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: wait 2, 4, 8 seconds
                    wait_time = 2 ** (attempt + 1)
                    time.sleep(wait_time)
                    continue

        # All retries failed
        error_result = {
            'latitude': lat,
            'longitude': lon,
            'city': None,
            'state': None,
            'country': None,
            'country_code': None,
            'postcode': None,
            'display_name': None,
            'status': f'error: {str(last_error)}'
        }

        return error_result

    def _extract_city(self, address: Dict) -> Optional[str]:
        """
        Extract city name from address components.
        Tries multiple fields in order of preference.

        Args:
            address: Address dictionary from Nominatim response

        Returns:
            City name or None
        """
        city_fields = ['city', 'town', 'village', 'municipality', 'hamlet']

        for field in city_fields:
            if field in address:
                return address[field]

        return None

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hits, misses, and size
        """
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'size': len(self.cache),
            'total_requests': self.cache_hits + self.cache_misses
        }

    def clear_cache(self):
        """Clear the cache and reset statistics."""
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def process_csv(self, input_file: str, output_file: str,
                   lat_column: str = 'latitude', lon_column: str = 'longitude') -> Tuple[int, int]:
        """
        Process a CSV file with coordinates and add geocoded information.

        Args:
            input_file: Path to input CSV file
            lat_column: Name of the latitude column
            lon_column: Name of the longitude column
            output_file: Path to output CSV file

        Returns:
            Tuple of (successful_count, total_count)
        """
        # Read the CSV file
        df = pd.read_csv(input_file)

        # Validate columns exist
        if lat_column not in df.columns or lon_column not in df.columns:
            raise ValueError(f"Columns '{lat_column}' and/or '{lon_column}' not found in CSV")

        # Initialize result columns
        results = []

        total_count = len(df)
        successful_count = 0

        # Process each row
        for idx, row in df.iterrows():
            lat = row[lat_column]
            lon = row[lon_column]

            result = self.reverse_geocode(lat, lon)
            results.append(result)

            if result['status'] == 'success':
                successful_count += 1

        # Create results dataframe
        results_df = pd.DataFrame(results)

        # Merge with original dataframe
        output_df = pd.concat([df, results_df.drop(['latitude', 'longitude'], axis=1)], axis=1)

        # Save to output file
        output_df.to_csv(output_file, index=False)

        return successful_count, total_count
