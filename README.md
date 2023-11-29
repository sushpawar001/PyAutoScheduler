PyAutoScheduler is a Python application designed to automate the scheduling of lectures based on user-provided constraints. This application is especially useful for educational institutions looking to efficiently allocate professors, subjects, and classes within specified departments and years.

## Features

- **User-Friendly Interface**: Easily input data, import data from CSV files, and configure department settings through a simple and intuitive interface.

- **Flexible Data Entry**: Provide information about departments, years/classes, professors, and subjects to tailor the scheduling process to your institution's specific needs.

- **CSV Import**: Streamline data entry by importing information from CSV files. A sample structure for the CSV file is provided for user convenience.

- **Customizable Timings**: Adjust college timings according to departments using the dedicated "Department Settings" tab.

- **Export Functionality**: Export generated timetables in both PDF and CSV formats from the "Export Timetable" tab for convenient sharing and record-keeping.

## Constraints

### Fully Satisfied Constraints

1. **Professor Allocation**: No professor will be allocated to two different classes simultaneously.

2. **Subject Allocation**: One subject cannot be allocated to two different professors in the same year/class.

3. **Workload Management**: The app ensures that the number of lectures per week for a professor per subject (workload) does not exceed specified limits.

### Partially Satisfied Constraints

1. **Incomplete Slot Filling**: All slots of classes may not be filled. If there are no available professors, a slot will remain empty.

## Getting Started

To use PyAutoScheduler, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/sushpawar001/PyAutoScheduler.git
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the main application:

   ```bash
   python main.py
   ```

## Usage Instructions

1. Navigate to the "Options" tab.
2. Use the "Add Data" tab to manually input information or the "Import CSV" tab to import data from a CSV file.
3. Adjust college timings based on departments in the "Department Settings" tab.
4. Generate timetables in PDF or CSV format in the "Export Timetable" tab.

## Note

- Ensure that you have Python installed on your system before running the application.

Feel free to explore, contribute, and enhance PyAutoScheduler to better suit your scheduling needs. Happy scheduling!