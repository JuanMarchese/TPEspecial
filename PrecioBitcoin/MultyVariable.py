import pandas as pd
import numpy as np

from AuxiliaryFunctions import get_plot_and_data, string_to_datetime, to_datetime, calculate_bitcoin_cost

from bokeh.models import Select, DateRangeSlider
from bokeh.layouts import column, row
from bokeh.io import curdoc

variable_path = "./variables/"

var_data = {
            "CostoTransaccion":       {"Y": "USD",
                                       "file": "cost-transaction.csv"},
            "Dificultad":             {"Y": "deficultad",
                                       "file": "difficulty.csv"},
            "DireccionesUnicas":      {"Y": "N",
                                       "file": "direcciones-unicas.csv"},
            "HashRate":               {"Y": "HashRate",
                                       "file": "hashrate.csv"},
            "GananciaMineros":        {"Y": "USD",
                                       "file": "miners-revenue.csv"},
            "Transacciones":          {"Y": "N",
                                       "file": "number-transactions.csv"},
            "TotalBitcoins":          {"Y": "N",
                                       "file": "total-bitcoin.csv"},
            "VolumenTransacciones":   {"Y": "USD",
                                       "file": "transaction-volume.csv"},
            "Valor":                  {"Y": "USD",
                                       "file": "value-usd.csv"},
            "TotalIntercambiado":     {"Y": "USD",
                                       "file": "total-exchange.csv"},
            "HashRateCost":           {"Y": "USD",
                                       "file": "HashRateCost.csv"},
            "BitCoinCashHashRate":    {"Y": "USD",
                                       "file": "BitCoinCashHashRate.csv"}
          }


################################################################################
############################### Data loading ###################################
################################################################################

halving = pd.read_csv(variable_path + "halving.csv")
halving = halving["Dates"].values


def load_data(file_name):
    df = pd.read_csv(variable_path + file_name)
    df = df[df["Value"] > 0.0]
    df = df.sort_values(by='Date').reset_index()

    return df[["Date", "Value"]]


def change_plot(attr, old, new):

    var_id = old
    if old in var_to_selected:
        var_id = var_to_selected[old]

    var_to_selected[new] = var_id

    new_var = var_to_pos[new]

    data = var_data[var_list[new_var]]["data"]
    data_source_list[var_id].data = dict(x=to_datetime(data["Date"]),
                                         y=data["Value"])


for var_name in var_data.keys():
    var_data[var_name]["data"] = load_data(var_data[var_name]["file"])


var_data["BitcoinCost"] = {"Y": "USD"}
var_data["BitcoinCost"]["data"] = calculate_bitcoin_cost(var_data["HashRateCost"]["data"], var_data["HashRate"]["data"], 0.1)

plot_width = 1200
plot_height = 600

var_count = 3

plot_list = []
data_source_list = []
var_select_list = []

var_list = list(var_data.keys())
var_to_pos = {}
var_to_selected = {}

for i in range(len(var_list)):
    var_to_pos[var_list[i]] = i


for i in range(var_count):

    title = "Variable " + str(i)

    plot_var, data_source_var = get_plot_and_data(plot_width, plot_height, title, halving)
    var_select = Select(title=title, value=var_list[i], options=var_list)

    var_to_selected[var_list[i]] = i

    plot_list.append(plot_var)
    data_source_list.append(data_source_var)
    var_select_list.append(var_select)

    var_select_list[-1].on_change('value', change_plot)
    change_plot("value", i, var_list[i])


slider_date_range = DateRangeSlider(title="Rango años",
                                    start=string_to_datetime("2009-01-01"), end=string_to_datetime("2021-06-01"),
                                    value=(string_to_datetime("2009-01-01"), string_to_datetime("2021-06-01")))


controls = var_select_list + [slider_date_range]

inputs = column(*controls, width=280, height=750)
inputs.sizing_mode = "fixed"

plots = column(*plot_list)
main_panel = row(plots, inputs)
curdoc().add_root(main_panel)
curdoc().title = "Multi Variable"