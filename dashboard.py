import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px

# URLs for the datasets
url_confirmed = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
url_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
url_vaccinations = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"

# Load data
confirmed_data = pd.read_csv(url_confirmed)
deaths_data = pd.read_csv(url_deaths)
vaccination_data = pd.read_csv(url_vaccinations)

# Melt confirmed and deaths data for better handling
confirmed_data = confirmed_data.melt(
    id_vars=["Province/State", "Country/Region", "Lat", "Long"],
    var_name="Date", value_name="Confirmed Cases"
)
confirmed_data["Date"] = pd.to_datetime(confirmed_data["Date"])

deaths_data = deaths_data.melt(
    id_vars=["Province/State", "Country/Region", "Lat", "Long"],
    var_name="Date", value_name="Deaths"
)
deaths_data["Date"] = pd.to_datetime(deaths_data["Date"])

# Vaccination data processing
vaccination_data["Date"] = pd.to_datetime(vaccination_data["date"], errors="coerce")
vaccination_data = vaccination_data[["location", "Date", "total_vaccinations"]]
vaccination_data.rename(columns={"location": "Country"}, inplace=True)

# Combine data for country-level analysis
confirmed_summary = confirmed_data.groupby("Country/Region")["Confirmed Cases"].max().reset_index()
confirmed_summary.rename(columns={"Country/Region": "Country"}, inplace=True)

deaths_summary = deaths_data.groupby("Country/Region")["Deaths"].max().reset_index()
deaths_summary.rename(columns={"Country/Region": "Country"}, inplace=True)

vaccination_summary = vaccination_data.groupby("Country")["total_vaccinations"].max().reset_index()

# Merge summaries
country_data = confirmed_summary.merge(deaths_summary, on="Country", how="left")
country_data = country_data.merge(vaccination_summary, on="Country", how="left")
country_data["total_vaccinations"].fillna(0, inplace=True)

# Initialize Dash app
app = dash.Dash(name)

# App layout
app.layout = html.Div(
    style={"font-family": "Arial, sans-serif", "background-color": "#f4f4f9", "padding": "20px"},
    children=[
        html.Div(
            children=[
                html.H1(
                    "COVID-19 Global Trend Dashboard",
                    style={"textAlign": "center", "color": "#2c3e50", "font-size": "36px", "padding-bottom": "20px"}
                ),
                html.P(
                    "COVID-19 has profoundly impacted global lives and economies. This dashboard provides trends "
                    "in confirmed cases, deaths, and vaccinations across the world.",
                    style={"textAlign": "center", "font-size": "18px", "color": "#7f8c8d", "margin-bottom": "20px"}
                ),
            ]
        ),
        # Dropdowns for user selection
        html.Div(
            children=[
                dcc.Dropdown(
                    id="country-dropdown",
                    options=[{"label": country, "value": country} for country in country_data["Country"].unique()],
                    value="India",
                    style={
                        "width": "80%",
                        "margin": "auto",
                        "font-size": "16px",
                        "margin-bottom": "20px",
                        "background-color": "#ecf0f1",
                        "border-radius": "8px",
                        "padding": "10px"
                    }
                ),
                dcc.Dropdown(
                    id="data-dropdown",
                    options=[
                        {"label": "Confirmed Cases", "value": "Confirmed Cases"},
                        {"label": "Deaths", "value": "Deaths"},
                        {"label": "Vaccinations", "value": "total_vaccinations"}
                    ],
                    value="Confirmed Cases",
                    style={
                        "width": "80%",
                        "margin": "auto",
                        "font-size": "16px",
                        "margin-bottom": "30px",
                        "background-color": "#ecf0f1",
                        "border-radius": "8px",
                        "padding": "10px"
                    }
                ),
            ]
        ),
        # Graphs for visualization
        html.Div(
            children=[
                dcc.Graph(id="map-graph", config={"scrollZoom": True}),
                dcc.Graph(id="time-series-graph")
            ]
        )
    ]
)

# Callbacks for interactivity
@app.callback(
    [Output("map-graph", "figure"), Output("time-series-graph", "figure")],
    [Input("country-dropdown", "value"), Input("data-dropdown", "value")]
)
def update_visualizations(selected_country, selected_data):
    # Handle empty selection
    if not selected_country or not selected_data:
        return go.Figure(), go.Figure()

    # Create choropleth map
    map_figure = go.Figure(go.Choropleth(
        locations=country_data["Country"],
        locationmode="country names",
        z=country_data[selected_data],
        colorscale="Viridis",
        colorbar_title=selected_data
    ))
    map_figure.update_layout(
        title=f"Global {selected_data} Data",
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth")
    )

    # Filter time-series data
    if selected_data == "total_vaccinations":
        ts_data = vaccination_data[vaccination_data["Country"] == selected_country]
    elif selected_data == "Confirmed Cases":
        ts_data = confirmed_data[confirmed_data["Country/Region"] == selected_country]
    else:
        ts_data = deaths_data[deaths_data["Country/Region"] == selected_country]

    # Handle case of no data
    if ts_data.empty:
        return map_figure, go.Figure()

    # Create time-series graph
    time_series_figure = px.line(
        ts_data, x="Date", y=selected_data,
        title=f"{selected_data} Over Time in {selected_country}",
        labels={"Date": "Date", selected_data: selected_data}
    )
    time_series_figure.update_layout(template="plotly_dark")

    return map_figure, time_series_figure

# Run the server
if name == "main":
    app.run_server(debug=True)
