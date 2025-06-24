# Livepeer AI GPU and Capabilities Dashboard

A [Streamlit](https://streamlit.io/)-based web application to visualize GPU inventory
and AI capabilities across orchestrators in the Livepeer AI network using the Gateway
`/capabilities` endpoint.

## Features

- **GPU Type Distribution**: View the distribution of GPU types across orchestrators.
- **Orchestrator GPU Distribution**: Analyze GPU availability per orchestrator.
- **Capabilities Distribution**: Explore AI capabilities provided by the orchestrators.
- **Interactive Filters**: Filter data by GPU models and AI models.
- **Data Table**: View detailed GPU and orchestrator data in a tabular format.

## How to Run

1. Clone the repository:

    ```bash
    git clone https://github.com/rickstaa/ai-compute-visualizer
    cd ai-compute-visualizer
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set the required environment variable:

    ```bash
    export CAPABILITIES_DATA_URL="<GATEWAY_CAPABILITIES_URL>"
    ```

4. Run the application:

    ```bash
    streamlit run gpu_dashboard.py
    ```

5. Open your web browser and navigate to `http://localhost:8501` to view the dashboard.

## Deployment

To deploy the application on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the code to a GitHub repository.
2. Link the repository to Streamlit Community Cloud.
3. Set the environment variable `CAPABILITIES_DATA_URL` in the Streamlit Cloud settings
   to the appropriate gateway capabilities URL.

## Limitations

- Data represents a snapshot of orchestrators and capabilities at the time of parsing.
- Only GPUs ready to take jobs are shown.
- Data is collected from a single gateway and may not include all orchestrators and GPUs.
