"""Streamlit app to visualize GPU inventory and AI capabilities across orchestrators."""

import streamlit as st
import pandas as pd
import requests
import os
import plotly.express as px


CAPABILITIES_DATA_URL = os.getenv("CAPABILITIES_DATA_URL")
ENS_DATA_URL = "https://explorer.livepeer.org/api/ens-data"

if not CAPABILITIES_DATA_URL:
    raise EnvironmentError(
        "The CAPABILITIES_DATA_URL environment variable is not set. Please set it before running the application."
    )

def abbreviate_name(name: str, max_length: int = 15):
    """Abbreviates a name to a maximum length, adding ellipsis if it exceeds the limit.

    Args:
        name: The name to abbreviate.
        max_length: The maximum length of the name before abbreviation.
        
    Returns:
        The abbreviated name if it exceeds the max_length, otherwise the original name.
    """
    return name if len(name) <= max_length else name[:max_length] + "..."


@st.cache_data
def fetch_ens_data():
    """Fetches ENS data for orchestrators."""
    response = requests.get(ENS_DATA_URL)
    ens_data = response.json()
    return {
        entry["id"]: entry.get("name", entry["idShort"])
        for entry in ens_data
        if entry.get("name") is not None
    }


@st.cache_data
def load_capabilities_data():
    """Fetches and processes the capabilities data from the specified gateway."""
    response = requests.get(CAPABILITIES_DATA_URL)
    data = response.json()

    ens_mapping = fetch_ens_data()

    rows = []
    for orch in data["orchestrators"]:
        address = orch["address"]
        uri = orch["orch_uri"]
        capability_map = data["capabilities_names"]
        caps = orch.get("capabilities", {})
        constraints = caps.get("constraints", {}).get("PerCapability", {})
        hardware = orch.get("hardware") or []

        orch_name = ens_mapping.get(address.lower(), address)

        for hw in hardware:
            model = hw.get("model_id", "unknown")
            pipeline = hw.get("pipeline", "unknown")
            gpu_info = hw.get("gpu_info", {})
            for _, gpu in gpu_info.items():
                rows.append(
                    {
                        "Orchestrator": address,
                        "Orchestrator Name": orch_name,
                        "GPU Name": gpu["name"],
                        "GPU Total (GB)": round(gpu["memory_total"] / 1e9, 1),
                        "GPU Free (GB)": round(gpu["memory_free"] / 1e9, 1),
                        "Model": model,
                        "Pipeline": pipeline,
                        "orch_uri": uri,
                        "Capability": next(
                            (
                                capability_map.get(str(k))
                                for k, v in constraints.items()
                                if model in v.get("models", {})
                            ),
                            "unknown",
                        ),
                        "Warm": any(
                            model in v.get("models", {})
                            and v["models"][model].get("warm", False)
                            for v in constraints.values()
                        ),
                    }
                )
    return pd.DataFrame(rows)


st.title("Livepeer AI GPU and Job Dashboard")

if st.button("Reload Data"):
    st.cache_data.clear()
    df = load_capabilities_data()
else:
    df = load_capabilities_data()

st.markdown(
    "Explore the GPU resources and AI capabilities across the Livepeer AI network. "
    "This dashboard provides a detailed view of the compute landscape, including GPU "
    "distribution, capabilities, orchestrator-specific details, and insights into the "
    "`/capabilities` endpoint data."
)
st.markdown("<u>Limitations of the Data Source</u>", unsafe_allow_html=True)
st.markdown(
    """
    - **Snapshot of the Network:** Data represents a snapshot of orchestrators and
    capabilities as seen by the gateway at the time of parsing. Not all orchestrators
    may have been discovered.
    - **Active GPUs Only:** Only GPUs ready to take jobs are shown; attached but
    inactive GPUs are excluded.
    - **Gateway-Specific View:** Data is collected from a single gateway, which may not
    have visibility into all orchestrators and GPUs.
    - **Transcoding Network Exclusion:** GPUs part of the transcoding network are not
    included.
    - **Realtime AI GPUs Exclusion:** Still in beta and not discoverable on chain.
    """
)
st.markdown("<u>Future Improvements</u>", unsafe_allow_html=True)
st.markdown(
    """
    We plan to create a decentralized data aggregator to collect data from orchestrator
    and gateway nodes. This will provide a more complete and accurate picture of the
    compute landscape, improving visibility into GPUs, orchestrators, and capabilities
    across the network.
    """
)

total_gpus = df["GPU Name"].count()

gpu_models = df["GPU Name"].unique()
model_ids = df["Model"].unique()
with st.sidebar:
    selected_gpu = st.multiselect("GPU Model", gpu_models, default=list(gpu_models))
    selected_model = st.multiselect("AI Model", model_ids, default=list(model_ids))
df_filtered = df[df["GPU Name"].isin(selected_gpu) & df["Model"].isin(selected_model)]

st.subheader("GPU Type Distribution")
st.markdown(f"**Total GPUs:** {total_gpus}")
gpu_distribution = df_filtered["GPU Name"].value_counts().reset_index()
gpu_distribution.columns = ["GPU Name", "Count"]
gpu_pie_chart = px.pie(
    gpu_distribution,
    names="GPU Name",
    values="Count",
    hole=0.3,
)
st.plotly_chart(gpu_pie_chart, use_container_width=True)
gpu_bar_chart = px.bar(
    gpu_distribution,
    x="GPU Name",
    y="Count",
    labels={"GPU Name": "GPU Model", "Count": "Count"},
    text="Count",
)
gpu_bar_chart.update_traces(textposition="outside")
gpu_bar_chart.update_layout(
    xaxis_title="GPU Model",
    yaxis_title="Count",
    showlegend=False,
)
st.plotly_chart(gpu_bar_chart, use_container_width=True)

st.subheader("Orchestrator GPU Distribution")
st.markdown("**Total Orchestrators:** {}".format(df_filtered["Orchestrator"].nunique()))
gpus_per_orchestrator = (
    df_filtered.groupby(["Orchestrator", "Orchestrator Name"])["GPU Name"].count().reset_index()
)
gpus_per_orchestrator.columns = ["Orchestrator", "Orchestrator Name", "GPU Count"]
gpus_per_orchestrator = gpus_per_orchestrator.sort_values(by="GPU Count", ascending=False)
gpus_per_orchestrator["Orchestrator Name"] = gpus_per_orchestrator["Orchestrator Name"].apply(
    lambda name: abbreviate_name(name)
)
orch_pie_chart = px.pie(
    gpus_per_orchestrator,
    names="Orchestrator Name",
    values="GPU Count",
    hole=0.3,
)
st.plotly_chart(orch_pie_chart, use_container_width=True)
orch_bar_chart = px.bar(
    gpus_per_orchestrator,
    x="Orchestrator Name",
    y="GPU Count",
    labels={"Orchestrator Name": "Orchestrator Name", "GPU Count": "GPU Count"},
    text="GPU Count",
)
orch_bar_chart.update_traces(textposition="outside")
orch_bar_chart.update_layout(
    xaxis_title="Orchestrator Name",
    yaxis_title="GPU Count",
    showlegend=False,
)
st.plotly_chart(orch_bar_chart, use_container_width=True)

st.subheader("Capabilities Distribution")
st.markdown("**Total Capabilities:** {}".format(df_filtered["Capability"].nunique()))
capabilities_distribution = df_filtered["Capability"].value_counts().reset_index()
capabilities_distribution.columns = ["Capability", "Count"]
capabilities_pie_chart = px.pie(
    capabilities_distribution,
    names="Capability",
    values="Count",
    hole=0.3,
)
st.plotly_chart(capabilities_pie_chart, use_container_width=True)
capabilities_bar_chart = px.bar(
    capabilities_distribution,
    x="Capability",
    y="Count",
    labels={"Capability": "Capability Name", "Count": "Count"},
    text="Count",
)
capabilities_bar_chart.update_traces(textposition="outside")
capabilities_bar_chart.update_layout(
    xaxis_title="Capability Name",
    yaxis_title="Count",
    showlegend=False,
)
st.plotly_chart(capabilities_bar_chart, use_container_width=True)

st.subheader("Data Table")
st.dataframe(
    df_filtered.sort_values(by=["GPU Name", "Model"], ascending=False),
    use_container_width=True,
)
