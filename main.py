import streamlit as st
import pdfplumber
import os
import re

# Set Streamlit page configuration
st.set_page_config(
    layout="wide",
    page_title="UBER PDF to CSV Processor",
    page_icon="🚗"
)


def extract_data_from_pdf(pdf_file):
    # Initialize a dictionary to hold extracted data
    extracted_data = {
        'Date of Invoice': 'Not Available',
        'Driver Name': 'Not Available',
        'Vehicle License Plate': 'Not Available',
        'Service Type': 'Not Available',
        'Trip Distance': 'Not Available',
        'Trip Duration': 'Not Available',
        'Pickup Address': 'Not Available',
        'Dropoff Address': 'Not Available',
        'Trip Fare': 'Not Available',
        'Booking Fee': 'Not Available',
        'Tips': 'Not Available',
        'Taxes (HST)': 'Not Available',
        'Total Amount': 'Not Available',
        'Payment Method': 'Not Available',
        'Card Charged Date': 'Not Available',
        'Toronto Fee Recovery Surcharges': 'Not Available',
        'Toronto Accessibility Fee Recovery Surcharges': 'Not Available',
        'Rider Name': 'Not Available'  # Additional field based on the heading
    }

    with pdfplumber.open(pdf_file) as pdf:
        all_text = []
        for page in pdf.pages:
            text = page.extract_text()
            all_text.append(text)

        # Combine text from all pages
        text = "\n".join(all_text)

        # Implementing other patterns
        # You will need to define these patterns based on your PDFs' structure
        patterns = {
            'Rider Name': r"Thanks for tipping, (.*)",
            'Date of Invoice': r"(\w+ \d{1,2}, \d{4})",
            'Driver Name': r"You rode with (.*)",
            'Vehicle License Plate': r"License Plate: (.*)",
            'Service Type, Distance, and Duration': r"(UberX|UberPool|UberXL|UberBlack|UberSUV)\s+(\d+\.\d+) kilometers \| (\d+)",
            'Pickup and Dropoff': r"(\d{1,2}:\d{2} [AP]M \| .*)",
            'Trip Fare': r"Trip fare CA\$(\d+\.\d+)",
            'Booking Fee': r"Booking Fee CA\$(\d+\.\d+)",
            'Tips': r"Tips CA\$(\d+\.\d+)",
            'Toronto Fee Recovery Surcharges': r"Toronto Fee Recovery Surcharges CA\$(\d+\.\d+)",
            'Toronto Accessibility Fee Recovery Surcharges': r"Toronto Accessibility Fee Recovery Surcharges CA\$(\d+\.\d+)",
            'Taxes (HST)': r"HST CA\$(\d+\.\d+)",
            'Total Amount': r"Total CA\$(\d+\.\d+)",
            'Payment Method': r"(Cash|Visa|Mastercard|American Express|PayPal)",
            'Card Charged Date': r"(\d{1,2}/\d{1,2}/\d{2,4} \d{1,2}:\d{2} [AP]M)",
            # ... Add all other patterns here ...
        }


    for key, pattern in patterns.items():
        if key == 'Service Type, Distance, and Duration':
            match = re.search(pattern, text)
            if match:
                extracted_data['Service Type'] = match.group(1).strip()
                extracted_data['Trip Distance'] = match.group(2).strip()
                extracted_data['Trip Duration'] = match.group(3).strip()
        elif key == 'Pickup and Dropoff':
            matches = re.findall(pattern, text)
            if matches:
                # First address
                extracted_data['Pickup Address'] = matches[0].strip()
                # Last address
                extracted_data['Dropoff Address'] = matches[-1].strip()
        else:
            match = re.search(pattern, text)
            if match:
                extracted_data[key] = match.group(1).strip()
                
    return extracted_data
                    
def test_extract_data_from_pdf():
    #lets test
    pdf_file = 'sample.pdf'
    extracted_data = extract_data_from_pdf(pdf_file)
    assert extracted_data['Date of Invoice'] == 'June 1, 2021'
    assert extracted_data['Driver Name'] == 'John Doe'
    assert extracted_data['Vehicle License Plate'] == 'ABC123'
    assert extracted_data['Service Type'] == 'UberX'
    assert extracted_data['Trip Distance'] == '5.0'
    assert extracted_data['Trip Duration'] == '10'
    assert extracted_data['Pickup Address'] == '123 Main St, Toronto, ON'
    assert extracted_data['Dropoff Address'] == '456 Queen St, Toronto, ON'
    assert extracted_data['Trip Fare'] == '10.00'
    assert extracted_data['Booking Fee'] == '2.00'
    assert extracted_data['Tips'] == '1.00'

    print('All tests passed!')



def create_csv(data, output_csv_path):
    # Convert the data into a DataFrame and then to CSV using the exact column headers
    df = pd.DataFrame(data)
    df.to_csv(output_csv_path, index=False)
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
        for uploaded_file in uploaded_files:
            try:
                bytes_data = uploaded_file.read()
                # Save the uploaded file temporarily for processing
                with open(uploaded_file.name, "wb") as f:
                    f.write(bytes_data)

                # Extract data from PDF
                extracted_data = extract_data_from_pdf(uploaded_file.name)
                all_data.append(extracted_data)
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


# Style your Streamlit app
if __name__ == "__main__":
    main()
