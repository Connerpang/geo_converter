import streamlit as st
import pandas as pd
import os
from datetime import datetime
from geocoder import ReverseGeocoder
import tempfile


def main():
    st.set_page_config(
        page_title="Geo Converter - Reverse Geocoding",
        page_icon="🌍",
        layout="wide"
    )

    st.title("🌍 Geo Converter - Reverse Geocoding")
    st.markdown("Convert latitude/longitude coordinates to city names using OpenStreetMap Nominatim API")

    st.divider()

    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ Information")
        st.markdown("""
        **How to use:**
        1. Upload a CSV file with latitude and longitude columns
        2. Specify the column names (if different from defaults)
        3. Click 'Start Geocoding'
        4. Download the results

        **Optimizations:**
        - Automatic caching for duplicate coordinates
        - Auto-retry on failures (3 attempts)
        - Progress auto-save every 50 rows
        - Real-time ETA calculation
        - City names in English

        **Note:** The Nominatim API has a rate limit of 1 request per second.
        For 600 unique coordinates, expect ~10 minutes processing time.
        Duplicate coordinates are processed instantly via cache.
        """)

        st.divider()

        st.header("⚙️ Configuration")
        lat_column = st.text_input("Latitude Column Name", value="latitude")
        lon_column = st.text_input("Longitude Column Name", value="longitude")

    # Main content area
    uploaded_file = st.file_uploader("Upload CSV file with coordinates", type=['csv'])

    if uploaded_file is not None:
        try:
            # Read and display preview
            df = pd.read_csv(uploaded_file)

            st.success(f"✅ File uploaded successfully! Found {len(df)} rows.")

            # Display preview
            st.subheader("📊 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)

            # Create case-insensitive column mapping
            column_map = {col.lower(): col for col in df.columns}

            # Find actual column names (case-insensitive)
            actual_lat_column = column_map.get(lat_column.lower())
            actual_lon_column = column_map.get(lon_column.lower())

            # Validate columns
            if actual_lat_column is None or actual_lon_column is None:
                st.error(f"❌ Columns '{lat_column}' and/or '{lon_column}' not found in CSV file!")
                st.info(f"Available columns: {', '.join(df.columns)}")
                return

            st.success(f"✅ Found required columns: '{actual_lat_column}' and '{actual_lon_column}'")

            # Show sample coordinates
            st.subheader("📍 Sample Coordinates")
            sample_df = df[[actual_lat_column, actual_lon_column]].head(5)
            st.dataframe(sample_df, use_container_width=True)

            # Start geocoding button
            st.divider()

            if st.button("🚀 Start Geocoding", type="primary"):
                process_geocoding(uploaded_file, df, actual_lat_column, actual_lon_column)

        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please make sure you've uploaded a valid CSV file.")


def process_geocoding(uploaded_file, df, lat_column, lon_column):
    """
    Process the geocoding and display results with enhanced progress tracking.
    """
    st.subheader("🔄 Processing")

    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    stats_container = st.empty()

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_input:
            uploaded_file.seek(0)
            tmp_input.write(uploaded_file.read())
            input_path = tmp_input.name

        # Create output file path
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_output:
            output_path = tmp_output.name

        # Initialize geocoder
        geocoder = ReverseGeocoder()

        total_rows = len(df)
        processed = 0
        start_time = datetime.now()
        batch_save_interval = 50  # Save progress every 50 rows

        # Create results list
        results = []

        # Process each row
        for idx, row in df.iterrows():
            lat = row[lat_column]
            lon = row[lon_column]

            # Calculate ETA
            if processed > 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time_per_row = elapsed / processed
                remaining_rows = total_rows - processed
                eta_seconds = avg_time_per_row * remaining_rows
                eta_minutes = int(eta_seconds / 60)
                eta_seconds_remaining = int(eta_seconds % 60)
                eta_str = f"{eta_minutes}m {eta_seconds_remaining}s"
            else:
                eta_str = "calculating..."

            # Update status
            status_text.text(f"Processing row {idx + 1} of {total_rows} | ETA: {eta_str} | Cache hits: {geocoder.cache_hits} | API calls: {geocoder.cache_misses}")

            result = geocoder.reverse_geocode(lat, lon)
            results.append(result)

            processed += 1
            progress_bar.progress(processed / total_rows)

            # Batch save progress to prevent data loss
            if processed % batch_save_interval == 0 or processed == total_rows:
                # Create intermediate results dataframe
                temp_results_df = pd.DataFrame(results)
                temp_output_df = pd.concat([df.iloc[:processed], temp_results_df.drop(['latitude', 'longitude'], axis=1)], axis=1)
                temp_output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
                stats_container.caption(f"💾 Progress auto-saved at row {processed}")

        # Create results dataframe
        results_df = pd.DataFrame(results)

        # Merge with original dataframe
        output_df = pd.concat([df, results_df.drop(['latitude', 'longitude'], axis=1)], axis=1)

        # Save results with UTF-8 encoding
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Calculate final statistics
        successful_count = sum(1 for r in results if r['status'] == 'success')
        total_time = (datetime.now() - start_time).total_seconds()
        cache_efficiency = (geocoder.cache_hits / total_rows * 100) if total_rows > 0 else 0

        # Show success message with performance stats
        st.success(f"✅ Geocoding complete! Successfully processed {successful_count} out of {total_rows} rows in {int(total_time)}s.")

        if geocoder.cache_hits > 0:
            st.info(f"⚡ Cache saved {geocoder.cache_hits} API calls ({cache_efficiency:.1f}% efficiency) - Duplicate coordinates were processed instantly!")

        # Display results
        st.subheader("📊 Results")
        st.dataframe(output_df, use_container_width=True)

        # Show statistics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Rows", total_rows)
        with col2:
            st.metric("Successful", successful_count)
        with col3:
            st.metric("Failed", total_rows - successful_count)
        with col4:
            success_rate = (successful_count / total_rows * 100) if total_rows > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col5:
            st.metric("Cache Hits", f"{geocoder.cache_hits} ({cache_efficiency:.0f}%)")

        # Download button
        st.divider()
        st.subheader("💾 Download Results")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"geocoded_results_{timestamp}.csv"

        with open(output_path, 'rb') as f:
            st.download_button(
                label="📥 Download CSV",
                data=f,
                file_name=output_filename,
                mime="text/csv",
                type="primary"
            )

        # Clean up temporary files
        os.unlink(input_path)
        os.unlink(output_path)

    except Exception as e:
        st.error(f"❌ Error during geocoding: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()
