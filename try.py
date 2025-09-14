import streamlit as st  # type: ignore
import pandas as pd
from data_insights import generate_summary, load_dataset
from query_processor import process_query, process_NLP_query
from code_executor import run_generated_code
import warnings

warnings.filterwarnings("ignore")

# --- SIDEBAR WITH CONTROLS AND APP INFO ---
with st.sidebar:
    st.header("App Controls")
    if st.button("Clear Uploaded File", help="Removes the uploaded file and resets the app."):
        st.session_state["uploaded_file"] = None

    # Place grouped controls for clarity and add tooltips
    st.button("Settings", help="Configure display or app options (future feature)")
    st.button("Print", help="Print current page")
    st.button("About", help="Learn more about this app and its author")
    st.button("Developer Options", help="Access advanced options (future feature)")
    st.button("Clear Cache", help="Clear cached information")

    st.markdown("---")
    st.markdown("<small>**Data Navigator v1.0**<br>Made with ❤️ by Nachiket Kapure.</small>", unsafe_allow_html=True)

st.title("Data Navigator: Simplify Exploration")
st.markdown("Easily upload and explore your CSV or Excel data. Visualize patterns, generate insights, and chat with your dataset!")

# --- DISTINGUISHABLE UPLOADER WITH FEEDBACK ---
uploader_area = st.container()
with uploader_area:
    uploaded_file = st.file_uploader(" ", type=["csv", "xlsx", "xls"], key="file_upload")

# --- FILE PREFLIGHT & ERROR HANDLING ---
if uploaded_file:
    file_ok = True
    if uploaded_file.size > 200 * 1024 * 1024:
        st.error("File exceeds 200MB size limit. Please upload a smaller file.")
        file_ok = False

    # Add extension/type handling if needed

    if file_ok:
        try:
            dataset = load_dataset(uploaded_file)
            st.success(f"File uploaded: **{uploaded_file.name}** ({uploaded_file.size/1024:.1f} KB)")
            data_summary = generate_summary(dataset)

            tab1, tab2 = st.tabs(["📊 Data Overview", "💬 Chat with Data"])

            with tab1:
                st.write("### Dataset Snapshot:")
                st.dataframe(dataset.head())

                if st.checkbox("View Detailed Data Insights"):
                    insights_tabs = st.tabs(
                        ["Null Values", "Unique Values", "Duplicate Records", "Descriptive Stats", "Numeric Summary"]
                    )
                    with insights_tabs[0]:
                        null_counts = dataset.isnull().sum()
                        st.write("Null Values by Column:")
                        st.dataframe(null_counts)
                        st.write(f"**Total Null Values:** {null_counts.sum()}")

                    with insights_tabs[1]:
                        unique_counts = {col: dataset[col].nunique() for col in dataset.columns}
                        st.write("Unique Values by Column:")
                        st.dataframe(pd.DataFrame(list(unique_counts.items()), columns=["Column", "Unique Count"]))

                    with insights_tabs[2]:
                        duplicate_count = dataset.duplicated().sum()
                        st.write(f"**Total Duplicate Records:** {duplicate_count}")

                    with insights_tabs[3]:
                        st.write("Statistical Summary:")
                        st.dataframe(dataset.describe())

                    with insights_tabs[4]:
                        numeric_columns = dataset.select_dtypes(include="number")
                        if not numeric_columns.empty:
                            st.write("Numeric Column Summary:")
                            numeric_summary = numeric_columns.describe().T
                            st.dataframe(numeric_summary)
                        else:
                            st.write("No numeric columns in the dataset.")

                st.subheader("Generate Visualizations")
                viz_query = st.text_input("Describe a visualization (e.g., 'bar chart of sales by category'):")

                if viz_query:
                    with st.spinner("Generating visualization..."):
                        try:
                            generated_code = process_query(viz_query, data_summary)
                            execution_results, execution_output = run_generated_code(generated_code, dataset)
                            if "plt" in execution_results:
                                st.pyplot(execution_results["plt"].gcf())  # type: ignore
                            if isinstance(execution_results, str):
                                st.error(execution_results)
                            else:
                                st.success("Visualization created successfully!")
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

            with tab2:
                st.write("### Chat with Data Summary")
                query = st.text_input("Ask a question about the dataset:")
                if query:
                    with st.spinner("Analyzing your query..."):
                        try:
                            response = process_NLP_query(query, data_summary)
                            if any(keyword in response for keyword in ["import ", "plt.", "df."]):
                                if st.checkbox("Display Generated Code", key="chat_code"):
                                    st.code(response, language="python")
                                execution_results, execution_output = run_generated_code(response, dataset)
                                if execution_output:
                                    st.write("### Execution Output:")
                                    st.write(execution_output)
                                if "plt" in execution_results:
                                    st.pyplot(execution_results["plt"].gcf())  # type: ignore
                                if isinstance(execution_results, str):
                                    st.error(execution_results)
                                else:
                                    st.success("Query processed successfully!")
                            else:
                                st.write("### Answer:")
                                st.write(response)
                        except Exception as e:
                            st.error(f"Error processing query: {e}")
        except Exception as e:
            st.error(f"Error loading file: {e}")
else:
    st.info("No file uploaded. Please drag and drop a CSV or Excel file to start!")

