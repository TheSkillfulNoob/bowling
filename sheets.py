import streamlit as st
import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd
from result_ocr.ocr import compute_bowling_stats_from_string  # or wherever you put it
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

def sync_aggregates_from_full():
    """
    Reads every row in Bowling-full, computes its (Total, Pins, Strikes, Spares), 
    and appends the new ones to the Bowling sheet.
    """
    # 1) Read full detail sheet
    full = get_ground_truth_sheet().get_all_records()
    df_full = pd.DataFrame(full)
    if df_full.empty:
        return

    # 2) Compute stats from the game string
    df_full[['Total','Pins','Strikes','Spares']] = (
        df_full['Game String']
          .apply(compute_bowling_stats_from_string)
          .apply(pd.Series)
    )

    # 3) Read existing session sheet
    sess = pd.DataFrame(get_session_sheet().get_all_records())
    # Normalize date formats if needed
    sess['Date'] = pd.to_datetime(sess['Date'], dayfirst=True).dt.strftime('%Y/%m/%d')
    
    # 4) Find rows in full not already in sess by (Date, Location, Game)
    merged = df_full.merge(
        sess[['Date','Location','Game']], 
        on=['Date','Location','Game'], 
        how='left', indicator=True
    )
    to_add = merged[merged['_merge']=='left_only']

    if to_add.empty:
        return  # nothing new

    # 5) Append only the aggregate columns
    rows = to_add[['Date','Location','Game','Spares','Strikes','Pins','Total']].values.tolist()
    sheet = get_session_sheet()
    sheet.append_rows(rows, value_input_option='USER_ENTERED')
