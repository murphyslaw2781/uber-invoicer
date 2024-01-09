import streamlit as st
import pdfplumber
import pandas as pd
from datetime import datetime
import os
import re

# Set Streamlit page configuration
st.set_page_config(
    layout="wide",
    page_title="UBER PDF to CSV Processor",
    page_icon="🚗"
)


def extract_data_from_pdf(pdf_file, new_pattern=None):
    # Initialize a dictionary to hold extracted data
    personal_data = {
        'Date of Invoice': '',
        'Filename': os.path.basename(pdf_file),
        'Country': '',
        'Driver Name': '',
        'Vehicle License Plate': '',
        'Service Type': '',
        'Trip Distance': '',
        'Trip Duration': '',
        'Pickup Address': '',
        'Dropoff Address': '',
        'Payment Method': '',
        'Card Charged Date': '',
        'Rider Name': ''
    }

    with pdfplumber.open(pdf_file) as pdf:
        all_text = []
        for page in pdf.pages:
            text = page.extract_text()
            all_text.append(text)

        text = "\n".join(all_text)

        # Identify the country of the ride
        country = "Canada" if "Total CA$" in text else "USA"
        personal_data['Country'] = country

        # Define global patterns
        global_patterns = {
            'Rider Name': r"Thanks for tipping, (.*)",
            'Date of Invoice': r"(\w+ \d{1,2}, \d{4})",
            'Driver Name': r"You rode with (.*)",
            'Pickup and Dropoff': r"(\d{1,2}:\d{2} [AP]M) \| (.*)",
            # ... Add all other patterns here ...
        }
        # Define patterns for Canada
        patterns_ca = {
            'Service Type, Distance, and Duration': r"(UberX|UberPool|UberXL|UberBlack|UberSUV)\s+(\d+\.\d+) kilometers \| (\d+)",
            'Vehicle License Plate': r"License Plate: (.*)",
            'Trip Fare': r"(Trip fare|Normal Fare) CA\$(\d+\.\d+)",
            'Booking Fee': r"Booking Fee CA\$(\d+\.\d+)",
            'Distance': r"Distance CA\$(\d+\.\d+)",
            'Time': r"Time CA\$(\d+\.\d+)",
            'Base Fare': r"Base Fare CA\$(\d+\.\d+)",
            'Surge': r"Surge CA\$(\d+\.\d+)",
            'Surge x2': r"Surge x2 CA\$(\d+\.\d+)",
            'Wait Time': r"Wait Time CA\$(\d+\.\d+)",
            'Tips': r"Tips CA\$(\d+\.\d+)",
            'Promotion': r"Promotion -CA\$(\d+\.\d+)",
            'Toronto Fee Recovery Surcharges': r"Toronto Fee Recovery Surcharges CA\$(\d+\.\d+)",
            'Toronto Accessibility Fee Recovery Surcharges': r"Toronto Accessibility Fee Recovery Surcharges CA\$(\d+\.\d+)",
            'Mississauga Fee Recovery Surcharge': r"Mississauga Fee Recovery Surcharge CA\$(\d+\.\d+)",
            'Uber Airport Surcharge': r"Uber Airport Surcharge CA\$(\d+\.\d+)",
            'Taxes (HST)': r"HST CA\$(\d+\.\d+)",
            'Total Amount': r"Total CA\$(\d+\.\d+)",
            'Payment Method': r"(Cash|Visa|Mastercard|American Express|PayPal|Work card)",
            'Card Charged Date': r"(\d{1,2}/\d{1,2}/\d{2,4} \d{1,2}:\d{2} [AP]M)",

            # ... [Other Canadian-specific patterns] ...
        }

        # Define patterns for USA
        patterns_us = {
            'Service Type, Distance, and Duration': r"(UberX|UberPool|UberXL|UberBlack|UberSUV)\s+(\d+\.\d+) miles \| (\d+)",
            'Vehicle License Plate': r"License Plate: (.*)",
            'Trip Fare': r"(Trip fare|Normal Fare) \$(\d+\.\d+)",
            'Booking Fee': r"Booking Fee \$(\d+\.\d+)",
            'Distance': r"Distance CA\$(\d+\.\d+)",
            'Time': r"Time CA\$(\d+\.\d+)",
            'Base Fare': r"Base Fare CA\$(\d+\.\d+)",
            'Surge': r"Surge \$(\d+\.\d+)",
            'Wait Time': r"Wait Time \$(\d+\.\d+)",
            'Tips': r"Tips \$(\d+\.\d+)",
            'Toronto Fee Recovery Surcharges': r"Toronto Fee Recovery Surcharges \$(\d+\.\d+)",
            'Toronto Accessibility Fee Recovery Surcharges': r"Toronto Accessibility Fee Recovery Surcharges \$(\d+\.\d+)",
            'Colorado Prearranged Ride Regulatory Fee': r"Colorado Prearranged Ride Regulatory Fee \$(\d+\.\d+)",
            'Taxes (HST)': r"HST \$(\d+\.\d+)",
            'Total Amount': r"Total \$(\d+\.\d+)",
            'Payment Method': r"(Cash|Visa|Mastercard|American Express|PayPal|Work card)",
            'Card Charged Date': r"(\d{1,2}/\d{1,2}/\d{2,4} \d{1,2}:\d{2} [AP]M)",

        }

        # Choose the correct set of patterns based on the country
        patterns = patterns_ca if country == "Canada" else patterns_us
        # Add new pattern to the dictionary
        if new_pattern:
            patterns[new_pattern[0]] = new_pattern[1]
            print(patterns)
        # merge the global patterns with the country specific patterns
        patterns = {**global_patterns, **patterns}

        # Extraction logic
        for key, pattern in patterns.items():
            # check for missing patterns?
            all_missing_patterns = []
            missing_patterns = find_missing_patterns(text, patterns)
            all_missing_patterns.extend(missing_patterns)

            if key == 'Pickup and Dropoff':
                matches = re.findall(pattern, text)
                if matches:
                    # Extract pickup time and address
                    pickup_match = matches[0]
                    personal_data['Pickup Time'] = pickup_match[0].strip()
                    personal_data['Pickup Address'] = pickup_match[1].strip()

                    # Extract dropoff time and address
                    dropoff_match = matches[-1]
                    personal_data['Dropoff Time'] = dropoff_match[0].strip()
                    personal_data['Dropoff Address'] = dropoff_match[1].strip()

            else:
                match = re.search(pattern, text)
                if match:
                    if key == 'Service Type, Distance, and Duration':
                        personal_data['Service Type'] = match.group(1).strip()
                        personal_data['Trip Distance'] = match.group(2).strip()
                        personal_data['Trip Duration'] = match.group(3).strip()
                    elif key == 'Card Charged Date':
                        date_str = match.group(1).strip()
                        try:
                            # Adjust the format to match "MM/DD/YY H:MM AM/PM"
                            date_obj = datetime.strptime(
                                date_str, "%m/%d/%y %I:%M %p")
                            formatted_date = date_obj.strftime(
                                "%Y-%m-%d %H:%M")
                            personal_data[key] = formatted_date
                        except ValueError:
                            personal_data[key] = 'Invalid Date Format'
                    else:
                        personal_data[key] = match.group(1).strip()

    return personal_data, all_missing_patterns
# Create a CSV file from the extracted data


def find_missing_patterns(text, patterns):
    start_index = text.find("Total")
    end_index = text.find("Payments", start_index)
    missing_patterns = []

    if start_index != -1 and end_index != -1:
        relevant_text = text[start_index:end_index]
        for line in relevant_text.split('\n'):
            # Skip lines that contain "Subtotal"
            if "Subtotal" in line:
                continue
            if not any(re.search(pattern, line) for pattern in patterns.values()):
                missing_patterns.append(line)
    return missing_patterns


def create_csv(data, output_csv_path):
    # Convert the data into a DataFrame and then to CSV using the exact column headers
    df = pd.DataFrame(data)
    df.to_csv(output_csv_path, index=False)

    return output_csv_path


def update_csv_with_new_pattern(pdf_file, new_pattern, original_data, output_csv_path):
    # Extract data with the new pattern
    new_data, _ = extract_data_from_pdf(pdf_file, new_pattern=new_pattern)

    # Update the original data with new data
    for key in new_data.keys():
        original_data[key] = new_data[key]

    # Write updated data back to CSV
    create_csv(original_data, output_csv_path)

    return output_csv_path

# Define the main content of your app


def main():
    st.title('UBER PDF to CSV Processor')

    # Sidebar for file upload and processing button
    with st.sidebar:
        st.write("## Upload PDFs")
        uploaded_files = st.file_uploader(
            "Choose PDF files", accept_multiple_files=True, type=['pdf'])

        process_button = st.button('Process PDFs to CSV', key='process_button')

    # Main content area
    if process_button and uploaded_files:
        # Check for duplicate filenames
        filenames = [uploaded_file.name for uploaded_file in uploaded_files]
        if len(filenames) != len(set(filenames)):
            st.error(
                'Duplicate filenames detected. Please ensure all files have unique names.')
            st.stop()

        all_data = []
        all_missing_items = {}
        for uploaded_file in uploaded_files:
            try:
                bytes_data = uploaded_file.read()
                # Save the uploaded file temporarily for processing
                with open(uploaded_file.name, "wb") as f:
                    f.write(bytes_data)

                extracted_data, missing_patterns = extract_data_from_pdf(
                    uploaded_file.name)
                all_data.append(extracted_data)
                all_missing_items[uploaded_file.name] = missing_patterns
                # Remove the PDF file after processing
                os.remove(uploaded_file.name)

            except Exception as e:
                st.error(f'Error processing {uploaded_file.name}: {e}')
                continue  # Skip this file and continue with the next

        if all_data:  # Check if there's any data processed successfully
            output_csv_path = 'processed_data.csv'
            create_csv(all_data, output_csv_path)
            st.success('PDFs have been processed and converted to CSV!')

            df_display = pd.read_csv(output_csv_path)
            # Use st.dataframe for better table format
            st.dataframe(df_display)

            with open(output_csv_path, "rb") as file:
                st.download_button(
                    label="Download CSV",
                    data=file,
                    file_name="processed_data.csv",
                    mime="text/csv",
                )
        else:
            st.error(
                "No PDFs were processed successfully. Please check your files and try again.")
        with st.sidebar:
            if all_missing_items:
                st.write(f"### Missing Line Items:")
            # Interactive UI for missing patterns
            new_patterns = {}
            for file_name, missing_items in all_missing_items.items():
                missing_items = [item for item in missing_items if item != '']
                for item in missing_items:
                    new_pattern_key = item
                    new_pattern_value = f"r'{item} CA\$(\d+\.\d+)'"
                    new_pattern = (new_pattern_key, new_pattern_value)
                    new_patterns[file_name] = new_pattern
                    st.write(f"#### {item} \n *{file_name}*")


# Style your Streamlit app
if __name__ == "__main__":
    main()
