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
from bokeh.models import ColumnDataSource, Div, Select, CheckboxButtonGroup, DateRangeSlider, Slider, Segment, Quad, DataTable, DateFormatter, TableColumn, HoverTool


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
    data_temp["Value"] = data_temp["Value"].values / data_temp["Value"].values[0]

    if rolling_window > 0:
        values = data_temp["Value"].rolling(rolling_window).sum()
    else:
        values = data_temp["Value"]

    bitcoin_price_container.data = dict(x=to_datetime(data_temp["Date"].values),
                                        y=values)

    result = calculate_variations_and_window(values, data_temp["Date"], bitcoin_periods_container, outliers_container, histogram_container)

    shapiro_test = stats.shapiro(result)

    normal_test_container.data = dict(dias=[rolling_window],
                                      estadistico=[shapiro_test.statistic],
                                      p_valor=[shapiro_test.pvalue],
                                      kurtosis=[stats.kurtosis(result)],
                                      skew=[stats.skew(result)]
                                      )

    ups_x = data_temp[[x >= 1.0 for x in result]]["Date"].values
    ups_y = [x for x in result if x >= 1.0]

    downs_x = data_temp[[x < 1.0 for x in result]]["Date"].values
    downs_y = [x for x in result if x < 1.0]

    bitcoin_ups_container.data = dict(x=to_datetime(ups_x),
                                      y=ups_y)
    bitcoin_downs_container.data = dict(x=to_datetime(downs_x),
                                        y=downs_y)


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

slider_date_range = DateRangeSlider(title="Rango años",
                                 start=string_to_datetime(start_date), end=string_to_datetime(end_date),
                                 value=(string_to_datetime(start_date), string_to_datetime(end_date)))


slider_rolling_window = Slider(title="Rolling window",
                               start=0, end=60, value=0, step=1)

LABELS = ["Deflated"]
checkbox_button_group = CheckboxButtonGroup(labels=LABELS)

LABELS_2 = ["Kill"]
checkbox_button_group_kill = CheckboxButtonGroup(labels=LABELS_2)

#########################Data containers#########################

bitcoin_price_container = ColumnDataSource(data=dict(x=[], y=[]))
bitcoin_ups_container = ColumnDataSource(data=dict(x=[], y=[]))
bitcoin_downs_container = ColumnDataSource(data=dict(x=[], y=[]))

bitcoin_periods_container, outliers_container, histogram_container = get_box_plot_data_source()

normal_test_container = ColumnDataSource(data=dict(dias=[],
                                                   estadistico=[],
                                                   p_valor=[],
                                                   kurtosis=[],
                                                   skew=[]))

#########################Comparacion#########################

main_plot = figure(x_axis_type="datetime",
                   title="Precio Bitcoin (USD)",
                   plot_width=plot_width, plot_height=plot_height)

main_plot.grid.grid_line_alpha= 0.3
main_plot.xaxis.axis_label = 'Fecha'
main_plot.yaxis.axis_label = "$"

main_plot_legend = Legend()
main_plot.add_layout(main_plot_legend, 'right')
main_plot.legend.click_policy = "hide"

main_plot.line(source=bitcoin_price_container,
               x="x",
               y="y",
               color=HSL(60, 1.0, 0.5).to_rgb(),
               legend_label="Bitcoin price")

main_plot.add_tools(HoverTool(
                              tooltips=[('Fecha', '@x{%F}'),
                                        ('Precio', '@y')],
                              formatters={'@x': 'datetime'},
                              mode='vline'
                              ))

second_plot = figure(x_axis_type="datetime",
                     title="Precio Bitcoin (USD)",
                     plot_width=plot_width, plot_height=plot_height)


second_plot.grid.grid_line_alpha= 0.3
second_plot.xaxis.axis_label = 'Fecha'
second_plot.yaxis.axis_label = "Variacion"

second_plot_legend = Legend()
second_plot.add_layout(second_plot_legend, 'right')
second_plot.legend.click_policy = "hide"

second_plot.circle(source=bitcoin_ups_container,
                   x="x",
                   y="y",
                   color=HSL(120, 1.0, 0.5).to_rgb(),
                   legend_label="Precio suba")

second_plot.circle(source=bitcoin_downs_container,
                   x="x",
                   y="y",
                   color=HSL(0, 1.0, 0.5).to_rgb(),
                   legend_label="Precio baja")



# Boxplot

third_plot = figure(x_axis_type="datetime",
                    title="Períodos de suba o baja",
                    plot_width=plot_width, plot_height=plot_height)

third_plot.grid.grid_line_alpha= 0.3
third_plot.xaxis.axis_label = 'Fecha'
third_plot.yaxis.axis_label = "Variacion"


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

four_thplot = figure(title="Histograma",
                     plot_width=plot_width, plot_height=plot_height)

four_thplot.quad(source=histogram_container,
                 top="hist", bottom=0, left="left", right="right",
                 fill_color="color", line_color="white", alpha=0.5)

four_thplot.y_range.start = 0

four_thplot.xaxis.axis_label = 'Variacion'
four_thplot.yaxis.axis_label = 'Cantidad'
four_thplot.grid.grid_line_color = "white"


#### Tabla

columns = [
        TableColumn(field="dias", title="Días"),
        TableColumn(field="estadistico", title="Estadistico"),
        TableColumn(field="p_valor", title="P-Valor"),
        TableColumn(field="kurtosis", title="kurtosis"),
        TableColumn(field="skew", title="Asimetria")
    ]

data_table = DataTable(source=normal_test_container, columns=columns)

#########################Controles#########################

update()

controls = [slider_date_range, slider_rolling_window, checkbox_button_group, checkbox_button_group_kill, data_table]

slider_date_range.on_change('value', update_date_range)
slider_rolling_window.on_change('value', update_rolling_window)
checkbox_button_group.on_change('active', update_deflation)
checkbox_button_group_kill.on_change('active', kill_app)

inputs = column(*controls, width=280, height=750)
inputs.sizing_mode = "fixed"

plot_list = [main_plot, second_plot, third_plot, four_thplot]
plots = column(*plot_list)

###########################General###########################

main_panel = row(plots, inputs)

curdoc().add_root(main_panel)
curdoc().title = "Análisis exploratorio bitcoin"


