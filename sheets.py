import streamlit as st
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

def connect_to_workbook() -> gspread.Spreadsheet:
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("v4_resources")

def get_session_sheet():
    return connect_to_workbook().worksheet("Bowling")

def get_ground_truth_sheet():
    return connect_to_workbook().worksheet("Bowling-full")

def push_session_data(df):
    """
    Appends the rows of df to the bottom of the Bowling sheet,
    leaving the existing data intact.
    """
    sheet = get_session_sheet()
    # Convert DataFrame to list-of-lists
    rows = df.values.tolist()
    # Append under existing data
    sheet.append_rows(rows, value_input_option="USER_ENTERED")

def push_ground_truth(df):
    """
    Appends the rows of df to the bottom of the Bowling-full sheet.
    """
    sheet = get_ground_truth_sheet()
    rows = df.values.tolist()
    sheet.append_rows(rows, value_input_option="USER_ENTERED")