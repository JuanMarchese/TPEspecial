#### Constants

bitcoin_price_path = "variables/value-usd.csv"
path_cpi = "variables/US-CPI.csv"

plot_width = 1200
plot_height = 600

#### imports

from AuxiliaryFunctions import *

import pandas as pd
import numpy as np
from scipy import signal
import datetime
from dateutil.relativedelta import relativedelta

from bokeh.events import ButtonClick
from bokeh.models import ColumnDataSource, Select, Button
from bokeh.layouts import column, row
from bokeh.io import curdoc

#########################################

def update_first(attr, old, new):
    global first_serie
    first_serie = new
    update()


def update_second(attr, old, new):
    global second_serie
    second_serie = new
    update()

def next_second_serie():
    global second_serie

    new_pos = lista_nombres.index(second_serie) + 1
    if new_pos > len(lista_nombres):
        new_pos = 0

    second_serie = lista_nombres[new_pos]
    update()

def update():
    first_data = splited_data[first_serie]["data"]
    second_data = splited_data[second_serie]["data"]

    first_serie_container.data = dict(x=to_datetime(first_data["Date"]),
                                      y=first_data["Value_deflated"])

    second_serie_container.data = dict(x=to_datetime(second_data["Date"]),
                                       y=second_data["Value_deflated"])

    correlation = signal.correlate(first_data["Value_deflated"].values,
                                   second_data["Value_deflated"].values,
                                   mode='same',
                                   method='direct')

    start_plot = 0 - int(len(correlation) / 2)
    end_plot = len(correlation) + start_plot

    correlation_container.data = dict(x=[x for x in range(start_plot, end_plot)],
                                      y=correlation)


###########  data loading  ###########

bitcoin_price = pd.read_csv(bitcoin_price_path)
bitcoin_price = bitcoin_price.sort_values(by='Date').reset_index()
bitcoin_price["Date"] = [str(x) for x in bitcoin_price["Date"].values]
bitcoin_price = bitcoin_price[["Date", "Value"]]
bitcoin_price = bitcoin_price[bitcoin_price["Value"] > 0.0]


cpi = pd.read_csv(path_cpi)
cpi_values = cpi["Value"].values
cpi_dates = [datetime.datetime.strptime(x, "%Y-%m-%d") for x in cpi["Date"].values]

new_dates = []
new_values = []

for i in range(len(cpi_values) - 1):

    start_date = cpi_dates[i]
    start_value = cpi_values[i]

    days_delta = (cpi_dates[i + 1] - cpi_dates[i]).days
    value_increment = (cpi_values[i + 1] - cpi_values[i]) / days_delta

    for j in range(days_delta - 1):
        new_dates.append((start_date + datetime.timedelta(days=j)).strftime("%Y-%m-%d"))
        new_values.append(start_value + (value_increment * j))

for j in range(30):
    new_dates.append((cpi_dates[-1] + datetime.timedelta(days=j)).strftime("%Y-%m-%d"))
    new_values.append(cpi_values[-1])

new_cpi = pd.DataFrame({"Date": new_dates,
                        "CPI": new_values})


bitcoin_price = pd.merge(bitcoin_price, new_cpi, on="Date")
bitcoin_price["CPI"] = bitcoin_price["CPI"].values / bitcoin_price["CPI"].values[0]

bitcoin_price["Value_deflated"] = bitcoin_price["Value"] / bitcoin_price["CPI"]

bitcoin_price["Value"] = bitcoin_price["Value"].rolling(28).mean()
bitcoin_price["Value_deflated"] = bitcoin_price["Value"].rolling(28).mean()

##############################################

splited_data = {}

start = datetime.datetime.strptime(bitcoin_price["Date"].values[0], "%Y-%m-%d")
end = datetime.datetime.strptime("2011-01-01", "%Y-%m-%d")

finish = datetime.datetime.strptime(bitcoin_price["Date"].values[-1], "%Y-%m-%d")

while start < finish:
    delta = start + relativedelta(months=+12)

    start_str = start.strftime("%Y-%m-%d")
    end_str = delta.strftime("%Y-%m-%d")

    current_data = bitcoin_price[bitcoin_price["Date"] >= start_str]
    current_data = current_data[current_data["Date"] < end_str]

    name = start_str + "/" + end_str
    splited_data[name] = ({"start": start_str,
                           "end": end_str,
                           "data": current_data})

    start = end
    end = start + relativedelta(months=+6)



##############################################

first_serie_container = ColumnDataSource(data=dict(x=[], y=[]))
second_serie_container = ColumnDataSource(data=dict(x=[], y=[]))
correlation_container = ColumnDataSource(data=dict(x=[], y=[]))


##############################################


main_plot = get_generic_plot("Primera serie", "Fecha", "USD",
                             y_axis_money=True,
                             plot_width=1200, plot_height=350
                             )
main_plot.line(source=first_serie_container,
               x="x",
               y="y",
               color=RGB(0, 0, 256))
main_plot.add_tools(HoverTool(
                              tooltips=[('Fecha', '@x{%F}'),
                                        ('Precio', '@y')],
                              formatters={'@x': 'datetime'},
                              mode='vline'
                              ))


second_plot = get_generic_plot("Segunda serie", "Fecha", "USD",
                               y_axis_money=True,
                               plot_width=1200, plot_height=350
                               )
second_plot.line(source=second_serie_container,
                 x="x",
                 y="y",
                 color=RGB(0, 0, 256))
second_plot.add_tools(HoverTool(
                              tooltips=[('Fecha', '@x{%F}'),
                                        ('Precio', '@y')],
                              formatters={'@x': 'datetime'},
                              mode='vline'
                              ))

third_plot = get_generic_plot("Correlacion", "Fecha", "USD",
                              y_axis_money=False,
                              x_axis_is_date=False,
                              plot_width=1200, plot_height=400
                              )
third_plot.line(source=correlation_container,
                x="x",
                y="y",
                color=RGB(0, 0, 256))

##############################################

lista_nombres = list(splited_data.keys())

first_serie_select = Select(title="Primera serie", value=lista_nombres[0], options=lista_nombres)
second_serie_select = Select(title="Primera serie", value=lista_nombres[1], options=lista_nombres)
button = Button(label="Siguiente", button_type="success")


first_serie_select.on_change('value', update_first)
second_serie_select.on_change('value', update_second)
button.on_event(ButtonClick, next_second_serie)

first_serie = lista_nombres[0]
second_serie = lista_nombres[1]



#########################Controles#########################

update()

controls = [first_serie_select, second_serie_select, button]
inputs = column(*controls, width=280, height=750)
inputs.sizing_mode = "fixed"

plot_list = [main_plot, second_plot, third_plot]
plots = column(*plot_list)

###########################General###########################

main_panel = row(plots, inputs)

curdoc().add_root(main_panel)
curdoc().title = "Análisis exploratorio bitcoin"


