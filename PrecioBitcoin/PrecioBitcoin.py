#### Constants

bitcoin_price_path = "variables/value-usd.csv"
path_cpi = "variables/US-CPI.csv"

plot_width = 1200
plot_height = 600

##### Imports
import pandas as pd
import numpy as np
import datetime
from scipy import stats
import sys

#### Imports for Bokeh

from bokeh.models import Span
from bokeh.layouts import gridplot
from bokeh.plotting import figure, output_notebook, show
from bokeh.colors import HSL, RGB
from bokeh.models import Legend


from bokeh.layouts import column, row, layout
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Div, Select, CheckboxButtonGroup, DateRangeSlider, Slider, Segment, Quad, DataTable, DateFormatter, TableColumn, HoverTool, Range1d


from AuxiliaryFunctions import *


def kill_app(attr, old, new):
    sys.exit()

##############################################


def update():
    data_temp = bitcoin_price[["Date", "Value"]]

    if 0 in checkbox_button_group.active:
        data_temp["Value"] = bitcoin_price["Value_deflated"]

    data_temp = data_temp[data_temp["Date"] >= start_date]
    data_temp = data_temp[data_temp["Date"] <= end_date]
    data_temp = data_temp.reset_index()
    data_temp["ValueOriginal"] = data_temp["Value"]
    data_temp["Value"] = data_temp["Value"].values / data_temp["Value"].values[0]

    if rolling_window > 0:
        data_temp["temp"] = data_temp["ValueOriginal"].rolling(rolling_window).mean()
        data_temp = data_temp[data_temp["temp"].notnull()]
        data_temp = data_temp.reset_index()

        values = data_temp["temp"].values
    else:
        values = data_temp["ValueOriginal"].values

    bitcoin_price_container.data = dict(x=to_datetime(data_temp["Date"].values),
                                        y=values)

    result = calculate_variations_and_window(values,
                                             data_temp["Date"],
                                             bitcoin_periods_container,
                                             outliers_container,
                                             histogram_container,
                                             box_size)

    shapiro_test = stats.shapiro(result)

    normal_test_container.data = dict(dias=[rolling_window],
                                      estadistico=[shapiro_test.statistic],
                                      p_valor=[shapiro_test.pvalue],
                                      kurtosis=[stats.kurtosis(result)],
                                      skew=[stats.skew(result)]
                                      )

    ups_x = data_temp[[x >= 0.0 for x in result]]["Date"].values
    ups_y = [x for x in result if x >= 0.0]

    downs_x = data_temp[[x < 0.0 for x in result]]["Date"].values
    downs_y = [x for x in result if x < 0.0]

    bitcoin_ups_container.data = dict(x=to_datetime(ups_x),
                                      y=ups_y)
    bitcoin_downs_container.data = dict(x=to_datetime(downs_x),
                                        y=downs_y)

    bitcoin_ups_downs_container.data = dict(x=to_datetime(data_temp["Date"].values),
                                        y=result)

    x_frecuencia_precio, y_frecuencia_precio = get_fft_transform(values)

    frecuencia_bitcoin_container.data = dict(x=x_frecuencia_precio,
                                             y=y_frecuencia_precio)

    x_frecuencia_variacion, y_frecuencia_variacion = get_fft_transform(result)
    frecuencia_variacion_container.data = dict(x=x_frecuencia_variacion,
                                               y=y_frecuencia_variacion)


def update_date_range(attr, old, new):
    global start_date
    global end_date
    start_date = datetime.datetime.fromtimestamp(new[0] / 1e3).strftime("%Y-%m-%d")
    end_date = datetime.datetime.fromtimestamp(new[1] / 1e3).strftime("%Y-%m-%d")

    update()


def update_rolling_window(attr, old, new):
    global rolling_window
    rolling_window = new
    update()


def update_box_size(attr, old, new):
    global box_size
    box_size = new
    update()


def update_deflation(attr, old, new):
    update()


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

#### Data loading

bitcoin_price = pd.read_csv(bitcoin_price_path)
bitcoin_price = bitcoin_price[bitcoin_price["Value"] > 0.0]
bitcoin_price = bitcoin_price.sort_values(by='Date').reset_index()

bitcoin_price = pd.merge(bitcoin_price, new_cpi, on="Date")
bitcoin_price["CPI"] = bitcoin_price["CPI"].values / bitcoin_price["CPI"].values[0]

bitcoin_price["Value_deflated"] = bitcoin_price["Value"] / bitcoin_price["CPI"]


###########################Correlation###########################


#########################Controls#########################

full_dates = to_datetime(bitcoin_price.Date.values)

start_year = int(bitcoin_price.Date.values[0][0:4])
end_year = int(bitcoin_price.Date.values[-1][0:4]) + 1

start_date = bitcoin_price.Date.values[0]
end_date = bitcoin_price.Date.values[-1]

rolling_window = 0
box_size = 30

slider_date_range = DateRangeSlider(title="Rango a??os",
                                 start=string_to_datetime(start_date), end=string_to_datetime(end_date),
                                 value=(string_to_datetime(start_date), string_to_datetime(end_date)))


slider_rolling_window = Slider(title="Rolling window",
                               start=0, end=60, value=0, step=1)

slider_box_size = Slider(title="Tama??o cajas",
                               start=30, end=360, value=30, step=30)

LABELS = ["Deflated"]
checkbox_button_group = CheckboxButtonGroup(labels=LABELS)

LABELS_2 = ["Kill"]
checkbox_button_group_kill = CheckboxButtonGroup(labels=LABELS_2)

#########################Data containers#########################

bitcoin_price_container = ColumnDataSource(data=dict(x=[], y=[]))
bitcoin_ups_container = ColumnDataSource(data=dict(x=[], y=[]))
bitcoin_downs_container = ColumnDataSource(data=dict(x=[], y=[]))
bitcoin_ups_downs_container = ColumnDataSource(data=dict(x=[], y=[]))

bitcoin_periods_container, outliers_container, histogram_container = get_box_plot_data_source()

normal_test_container = ColumnDataSource(data=dict(dias=[],
                                                   estadistico=[],
                                                   p_valor=[],
                                                   kurtosis=[],
                                                   skew=[]))

#########################Comparacion#########################

#main_plot = get_generic_plot("Precio Bitcoin (USD)", "Fecha", "USD", y_axis_money=True)
main_plot = get_generic_plot("Precio Bitcoin (USD Agosto 2010)", "Fecha", "USD Agosto 2010", y_axis_money=True)

main_plot.line(source=bitcoin_price_container,
               x="x",
               y="y",
               color=RGB(0, 0, 256))

main_plot.add_tools(HoverTool(
                              tooltips=[('Fecha', '@x{%F}'),
                                        ('Precio', '@y{$0,0}')],
                              formatters={'@x': 'datetime'},
                              mode='vline'
                              ))

main_plot.y_range = Range1d(-2000, 65000)
################


second_plot = get_generic_plot("Variacion precio Bitcoin", "Fecha", "Variacion", y_axis_money=False)
#second_plot.y_range = Range1d(-0.2, 0.2)


#second_plot_legend = Legend()
#second_plot.add_layout(second_plot_legend, 'right')
#second_plot.legend.click_policy = "hide"

second_plot.circle(source=bitcoin_ups_container,
                   x="x",
                   y="y",
                   color=HSL(120, 1.0, 0.5).to_rgb(),
                   size=2,
                   legend_label="Precio suba")

second_plot.circle(source=bitcoin_downs_container,
                   x="x",
                   y="y",
                   color=HSL(0, 1.0, 0.5).to_rgb(),
                   size=2,
                   legend_label="Precio baja")

second_plot.line(source=bitcoin_ups_downs_container,
                 x="x",
                 y="y",
                 color=RGB(0, 0, 0),
                 alpha=0.5,
                 line_width=0.5)

# Boxplot


third_plot = get_generic_plot("Per??odos de suba o baja", "Fecha", "Variacion", y_axis_money=False)

# stems
glyph = Segment(x0="x_position_middle", y0="upper_line_bottom", x1="x_position_middle", y1="upper_line_top", line_color="black")
third_plot.add_glyph(bitcoin_periods_container, glyph)

glyph = Segment(x0="x_position_middle", y0="down_line_bottom", x1="x_position_middle", y1="down_line_top", line_color="black")
third_plot.add_glyph(bitcoin_periods_container, glyph)

# boxes
glyph = Quad(left="x_position_start", right="x_position_end", top="upper_box_top", bottom="upper_box_bottom", fill_color="ligth_color")
third_plot.add_glyph(bitcoin_periods_container, glyph)

glyph = Quad(left="x_position_start", right="x_position_end", top="down_box_top", bottom="down_box_bottom", fill_color="dark_color")
third_plot.add_glyph(bitcoin_periods_container, glyph)

third_plot.circle(source=outliers_container,
                   x="outx",
                   y="outy",
                   color="black")


# Histogram

four_thplot = get_generic_plot("Histograma", "Variacion", "Cantidad", y_axis_money=False, x_axis_is_date=False)


four_thplot.quad(source=histogram_container,
                 top="hist", bottom=0, left="left", right="right",
                 fill_color="color", line_color="white", alpha=0.5)
four_thplot.y_range.start = 0
four_thplot.grid.grid_line_color = "white"

four_thplot.y_range = Range1d(0, 2300)
four_thplot.x_range = Range1d(-1, 1)


###### Frecuencia



frecuencia_bitcoin_container = ColumnDataSource(data=dict(x=[], y=[]))

frecuencia_variacion_container = ColumnDataSource(data=dict(x=[], y=[]))


frecuencia_bitcoin_plot = get_generic_plot("Respuesta en frecuencia de precio bitcoin", "", "", y_axis_money=False, x_axis_is_date=False)
frecuencia_bitcoin_plot.line(source=frecuencia_bitcoin_container,
                             x="x",
                             y="y",
                             color=RGB(0, 0, 512))

frecuencia_variacion_plot = get_generic_plot("Respuesta en frecuencia de variacion de precio", "", "", y_axis_money=False, x_axis_is_date=False)
frecuencia_variacion_plot.line(source=frecuencia_variacion_container,
                               x="x",
                               y="y",
                               color=RGB(0, 0, 512))


frecuencia_bitcoin_plot.add_tools(HoverTool(
                                              tooltips=[('Frecuencia', '@x'),
                                                        ('Energia', '@y')],
                                              mode='vline'
                                              ))

frecuencia_variacion_plot.add_tools(HoverTool(
                                              tooltips=[('Frecuencia', '@x'),
                                                        ('Energia', '@y')],
                                              mode='vline'
                                              ))


#### Tabla

columns = [
        TableColumn(field="dias", title="D??as"),
        TableColumn(field="estadistico", title="Estadistico"),
        TableColumn(field="p_valor", title="P-Valor"),
        TableColumn(field="kurtosis", title="kurtosis"),
        TableColumn(field="skew", title="Asimetria")
    ]

data_table = DataTable(source=normal_test_container, columns=columns)

#########################Controles#########################

update()

controls = [slider_date_range, slider_rolling_window, checkbox_button_group, checkbox_button_group_kill, data_table, slider_box_size]

slider_date_range.on_change('value', update_date_range)
slider_rolling_window.on_change('value', update_rolling_window)
slider_box_size.on_change('value', update_box_size)
checkbox_button_group.on_change('active', update_deflation)
checkbox_button_group_kill.on_change('active', kill_app)

inputs = column(*controls, width=280, height=750)
inputs.sizing_mode = "fixed"

plot_list = [main_plot, second_plot, third_plot, four_thplot, frecuencia_bitcoin_plot, frecuencia_variacion_plot]
plots = column(*plot_list)

###########################General###########################

main_panel = row(plots, inputs)

curdoc().add_root(main_panel)
curdoc().title = "An??lisis exploratorio bitcoin"


