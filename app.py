import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Completion Dashboard",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Function to Create Google Sheets CSV URL ---
def create_google_sheet_csv_url(url):
    """Converts a standard Google Sheet URL to a direct CSV download link."""
    # Use regex to extract the sheet ID from the URL
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        sheet_id = match.group(1)
        return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
    return None

# --- Title and Description ---
st.title("📊 Task Completion Dashboard")
st.markdown("""
This dashboard provides a visual overview of task completion status, automatically loaded from the project's Google Sheet.
""")

# --- Hardcoded Google Sheet URL ---
# The URL is now set here, so you don't need to enter it manually.
sheet_url = "https://docs.google.com/spreadsheets/d/1qwfADBf4R2owb9LbANpUiOZ2ZoQ9Tk9IpnPz1KAPpYQ/edit?usp=sharing"
st.sidebar.header("🔗 Data Source")
st.sidebar.info("Data is being loaded automatically from the pre-configured Google Sheet.")
st.sidebar.markdown(f"**[View Source Sheet]({sheet_url})**")


if sheet_url:
    try:
        csv_export_url = create_google_sheet_csv_url(sheet_url)
        
        if csv_export_url:
            # Read data directly from the Google Sheet URL
            df = pd.read_csv(csv_export_url)
            st.sidebar.success("Data loaded successfully! 🎉")

            # --- Data Cleaning and Preparation ---
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower()

            # Rename columns
            df.rename(columns={
                'sr.no.': 'sr_no',
                'd.o.r': 'date_of_receipt',
                'completion date': 'completion_date',
                'action taken': 'action_taken',
                'remarks': 'remarks'
            }, inplace=True)

            # Determine task status
            df['status'] = df['remarks'].apply(lambda x: 'Completed' if pd.notna(x) and str(x).strip() != '' else 'Pending')

            # Identify 'Tatkal' tasks
            # Ensure the 'priority' column exists before trying to access it
            if 'priority' in df.columns:
                df['is_tatkal'] = df['priority'].str.strip().str.lower() == 'tatkal'
            else:
                st.error("The 'priority' column was not found in your Google Sheet. Tatkal tasks cannot be identified.")
                df['is_tatkal'] = False # Create the column with False values

            # --- Main Dashboard Metrics ---
            st.header("Overall Task Summary")
            total_tasks = len(df)
            completed_tasks = df[df['status'] == 'Completed'].shape[0]
            pending_tasks = total_tasks - completed_tasks

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Tasks", value=total_tasks)
            with col2:
                st.metric(label="✅ Completed Tasks", value=completed_tasks, delta=f"{((completed_tasks/total_tasks)*100):.2f}%")
            with col3:
                st.metric(label="⏳ Pending Tasks", value=pending_tasks, delta=f"-{((pending_tasks/total_tasks)*100):.2f}%")

            st.markdown("---")

            # --- Tatkal (Urgent) Task Summary ---
            st.header("🚨 Tatkal (Urgent) Task Summary")
            tatkal_df = df[df['is_tatkal']].copy()
            total_tatkal_tasks = len(tatkal_df)

            if total_tatkal_tasks > 0:
                completed_tatkal_tasks = tatkal_df[tatkal_df['status'] == 'Completed'].shape[0]
                pending_tatkal_tasks = total_tatkal_tasks - completed_tatkal_tasks

                t_col1, t_col2, t_col3 = st.columns(3)
                with t_col1:
                    st.metric(label="Total Tatkal Tasks", value=total_tatkal_tasks)
                with t_col2:
                    st.metric(label="✅ Completed Tatkal", value=completed_tatkal_tasks, delta=f"{((completed_tatkal_tasks/total_tatkal_tasks)*100):.2f}%")
                with t_col3:
                    st.metric(label="⏳ Pending Tatkal", value=pending_tatkal_tasks, delta=f"-{((pending_tatkal_tasks/total_tatkal_tasks)*100):.2f}%")
            else:
                st.info("No 'Tatkal' tasks found in the data.")

            st.markdown("---")

            # --- Graphical Representations ---
            st.header("Visualizations")
            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                st.subheader("Overall Task Status")
                status_counts = df['status'].value_counts().reset_index()
                status_counts.columns = ['status', 'count']
                
                fig_status_pie = px.pie(
                    status_counts, names='status', values='count',
                    title='Overall Task Completion Status',
                    color='status', color_discrete_map={'Completed': '#4CAF50', 'Pending': '#F44336'},
                    hole=0.4
                )
                fig_status_pie.update_traces(textinfo='percent+label', pull=[0, 0.05])
                st.plotly_chart(fig_status_pie, use_container_width=True)

            with viz_col2:
                if total_tatkal_tasks > 0:
                    st.subheader("Tatkal Task Status")
                    tatkal_status_counts = tatkal_df['status'].value_counts().reset_index()
                    tatkal_status_counts.columns = ['status', 'count']

                    fig_tatkal_pie = px.pie(
                        tatkal_status_counts, names='status', values='count',
                        title='Tatkal Task Completion Status',
                        color='status', color_discrete_map={'Completed': '#2196F3', 'Pending': '#FF9800'},
                        hole=0.4
                    )
                    fig_tatkal_pie.update_traces(textinfo='percent+label', pull=[0, 0.05])
                    st.plotly_chart(fig_tatkal_pie, use_container_width=True)
                else:
                    st.subheader("Tatkal Task Status")
                    st.info("No 'Tatkal' tasks to visualize.")

            # --- Display Raw Data ---
            st.markdown("---")
            st.header("Raw Data View")
            st.dataframe(df)
        
        else:
            st.sidebar.error("The hardcoded URL appears to be invalid. Please check the script.")

    except Exception as e:
        st.sidebar.error("An error occurred while fetching or processing the data.")
        st.error(f"Error: {e}. Please ensure the Google Sheet is public ('Anyone with the link can view') and the URL is correct.")

