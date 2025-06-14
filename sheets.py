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
    sheet = get_session_sheet()
    set_with_dataframe(sheet, df)

def push_ground_truth(df):
    sheet = get_ground_truth_sheet()
    set_with_dataframe(sheet, df)