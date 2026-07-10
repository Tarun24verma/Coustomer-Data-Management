# Customer Data Manager

Customer Data Manager is a desktop application built with Python and Flet for creating and managing custom customer databases. It lets you define database schemas, store customer records, search them quickly, and keep each customer’s files in a dedicated folder.

## Features

- Create multiple customer databases
- Define custom fields for each database
- Add, search, and delete customer records
- Store customer document folders in a structured location
- Configure the storage folder for your databases
- Works as a lightweight desktop app

## Tech Stack

- Python
- Flet for the user interface
- SQLAlchemy for database access
- SQLite for local data storage
- PyInstaller support via the included spec file

## Project Structure

- main.py — Application entry point and UI
- database_manager.py — Database and file management logic
- config.json — Stores the selected base storage path
- requirements.txt — Python dependencies
- MyCustomerManager.spec — PyInstaller packaging configuration

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd "Coustomer Data Management"
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application with:

```bash
python main.py
```

When the app starts, you can:
- choose a storage folder for your databases
- create a new database and define its fields
- open an existing database
- add customer records and search through them

## Database Storage

By default, databases are stored under your user profile in a folder named MyCustomerDatabases. You can change this location from the app’s welcome screen.

## Build an Executable

To build a standalone Windows executable, run:

```bash
pyinstaller MyCustomerManager.spec
```

The generated build output will be placed in the build and dist folders.

## Notes

This project is intended for local use and stores data in SQLite files on disk. It is suitable for small to medium personal or team customer-management workflows.
