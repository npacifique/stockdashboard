import pandas as pd
import numpy as np
from dash import Dash, html, Output, Input, dcc, callback, ctx, State, dash_table
import plotly.graph_objects as go
import yfinance as yf
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# dbc_css = ("https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css")


def performance_tab_table(html, dbc):
    """
    Return the template used for the performance tab. Takes html and dbc
    """
    return (
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.P(
                            "This table presents a comprehensive analysis of the selected stock. It offers statistical details by aggregating the stock price to statically describe the trends shown in the chart."
                        )
                    ]
                ),
                dbc.CardBody(
                    [
                        html.Div(id="table-container"),
                    ]
                ),
            ]
        ),
    )


def chart_data(html, dbc, dcc):
    return (
        dbc.Card(
            [
                # display symbol input form in the card header
                dbc.CardHeader(
                    [
                        html.Div(
                            [
                                html.P(
                                    f"This dynamic chart showcases the trends of the selected stocks over the chosen period, visually presenting the performance of the stock at a glance. It aids in making informed investment decisions by highlighting trends."
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="symbol",
                                                    value="VTI",
                                                    type="text",
                                                    placeholder="Symbol",
                                                    className="form-control form-control-sm",
                                                ),
                                            ],
                                            className="col-3",
                                            style={"margin": "0px"},
                                        ),
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Find",
                                                    id="find",
                                                    n_clicks=0,
                                                    className="btn btn-primary btn-sm",
                                                )
                                            ],
                                            className="col",
                                            style={"margin-left": "-20px"},
                                        ),
                                    ],
                                    className="row",
                                ),
                                #
                                html.P(id="error_id", className="text-danger"),
                            ],
                            className="mb-2",
                        ),
                    ]
                ),
                # display figure in the card body
                dbc.CardBody(
                    [
                        dcc.Graph(id="graph"),
                    ],
                ),
                # display period selector in the card footer
                dbc.CardFooter(
                    [
                        html.Div(
                            generate_button(html),
                            style={"margin": "20px"},
                        ),
                    ]
                ),
            ]
        ),
    )


def generate_button(html):
    "generates buttons based on an array of button ids"
    return [
        html.Button(
            str(i).upper(),
            id=i,
            n_clicks=0,
            className="btn btn-sm",
            style={"marginRight": "8px"},
        )  # return button element for each id
        for i in ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    ]


def get_return(data):
    _gains = []
    for y in np.unique(data.index.year):

        _data = data.loc[data.index.year == y]
        _min = _data["Close"].min()
        _max = _data["Close"].max()
        _std = _data["Close"].std()
        _avg = _data["Close"].mean()
        _gain = f'{((_data.iloc[len(_data)-1]["Close"] - _data.iloc[0]["Close"]) /_data.iloc[len(_data)-1]["Close"] * 100).round(2)}%'
        _gains.append(
            {
                "Year": y,
                "Min": np.round(_min, decimals=2),
                "Max": np.round(_max, decimals=2),
                "Standard deviation": np.round(_std, decimals=2),
                "Price Avg": np.round(_avg, decimals=2),
                "Gain/Loss": _gain,
            }
        )

    return pd.DataFrame(_gains)


# app = Dash(external_stylesheets=[dbc.themes.DARKLY])
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
app.title = "Stock Analysis"
load_figure_template("SLATE")

def draw_figure(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=data["Close"], x=data.index))
    fig.update_layout(
        margin={"t": 0, "l": 10, "b": 0, "r": 10}
    )  # ,  template ='plotly_dark')
    return fig


def card_col(card_id, card_title):
    """
    Returns the cards displayed on top of the dashboard to show difference performance. takes value passed via html id,
    and the name of the card
    """
    return dbc.Col(
        dbc.Card(
            [dbc.CardBody([html.H4(id=card_id), html.P(card_title)])],
        )
    )


app.layout = dbc.Container(
    [
        html.H3(id="title_id", className="display-5 mb-2"),
        # reserved for performance cards
        dbc.Row(
            [
                card_col("price", "Market Price"),
                card_col("average", "Average Price"),
                card_col("gain", "Gain/Loss"),
            ],
            className="mb-2",
        ),
        dbc.Tabs(
            [
                dbc.Tab(
                    label="Trends",
                    children=[
                        html.Div(
                            chart_data(html, dbc, dcc),
                        )
                    ],
                ),
                dbc.Tab(
                    label="Performance",
                    children=[html.Div(performance_tab_table(html, dbc))],
                ),
            ]
        ),
    ],
    # className="dbc",
)


@callback(
    Output("graph", "figure"),
    Output("title_id", "children"),
    Output("error_id", "children"),
    Output("price", "children"),
    Output("average", "children"),
    Output("gain", "children"),
    Output("table-container", "children"),
    Input("5d", "n_clicks"),
    Input("1mo", "n_clicks"),
    Input("3mo", "n_clicks"),
    Input("6mo", "n_clicks"),
    Input("1y", "n_clicks"),
    Input("2y", "n_clicks"),
    Input("5y", "n_clicks"),
    Input("10y", "n_clicks"),
    Input("ytd", "n_clicks"),
    Input("max", "n_clicks"),
    State("symbol", "value"),
    Input("find", "n_clicks"),
)
def index(
    btn_5d,
    btn_1mo,
    btn_3mo,
    btn_6mo,
    btn_1y,
    btn_2y,
    btn_5y,
    btn_10y,
    btn_ytd,
    btn_max,
    value,
    find,
):
    # handle wrong input
    period = ""
    df = yf.Ticker(value).history(period="1Y")
    fig = draw_figure(df)
    error = ""
    price = "$00.00"
    data = None

    # handle find button clicked
    if ctx.triggered_id == "find":
        df = yf.Ticker(value).history(period="1Y")
        # fig = draw_figure(df)
        # data = get_return(df)

        if df.empty:
            error = f"No data found, symbol may be delisted"
        else:
            error = ""

        # fig = draw_figure(df)

    # handle button clicks
    print(ctx.triggered_id)
    if ctx.triggered_id == None or ctx.triggered_id == "find":
        period = "1Y"
        df = yf.Ticker(value).history(period="1y")
        # data = get_return(df)
        # fig = draw_figure(df)
    else:
        period = str(ctx.triggered_id).upper()
        df = yf.Ticker(value).history(period=ctx.triggered_id)
        # data = get_return(df)
        # fig = draw_figure(df)

    price = f'${np.round( df.iloc[len(df)-1]["Close"], decimals=2)}'
    average = f'${df["Close"].mean().round(2)}'

    # gain = (end_price - start_price) end_price * 100
    gain = (
        (
            (df.iloc[len(df) - 1]["Close"] - df.iloc[0]["Close"])
            / df.iloc[len(df) - 1]["Close"]
        )
        * 100
    ).round(2)

    data = get_return(df)
    fig = draw_figure(df)

    # table goes here
    table = dbc.Table.from_dataframe(
        data, striped=True, bordered=True, hover=True, color="dark", class_name="dbc"
    )

    return (
        fig,
        f"{str(value).upper()} ({period}) Stock Analysis",
        error,
        price,
        average,
        f"%{gain}",
        table,
    )


if __name__ == "__main__":
    app.run_server(debug=False)
