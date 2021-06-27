import pandas as pd
import numpy as np
import datetime

# Generic line plot
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Span, HoverTool
from bokeh.colors import RGB
from bokeh.models import NumeralTickFormatter





def to_datetime(x):
    return np.array(x, dtype=np.datetime64)


def string_to_datetime(x):
    return datetime.datetime.strptime(x, "%Y-%m-%d")


def same_sign(first, second, separation):

    if first < separation and second < separation:
        return True
    elif first >= separation and second >= separation:
        return True
    else:
        return False


def outliers(group):
    cat = group.name
    return group[(group.score > upper.loc[cat]['score']) | (group.score < lower.loc[cat]['score'])]['score']


####################################################################

# Box plot auxiliary

from bokeh.models import ColumnDataSource
from bokeh.colors import RGB


ligth_green = "#80FF80"
dark_green = "#408040"
ligth_red = "#FF8080"
dark_red = "#804040"


def get_box_plot_data_source():

    box_plot = ColumnDataSource(data=dict(upper_box_top=[],
                                          upper_box_bottom=[],
                                          down_box_top=[],
                                          down_box_bottom=[],
                                          upper_line_top=[],
                                          upper_line_bottom=[],
                                          down_line_top=[],
                                          down_line_bottom=[],
                                          x_position=[],
                                          ligth_color=[],
                                          dark_color=[]
                                          ))

    outliers = ColumnDataSource(data=dict(outx=[], outy=[]))

    histogram = ColumnDataSource(data=dict(hist=[],
                                           left=[],
                                           right=[],
                                           color=[]))

    return box_plot, outliers, histogram


def update_histogram_data_source(values, data_source):
    hist, edges = np.histogram(values, density=True, bins=50)

    colors = [ligth_green if x >= 1.0 else ligth_red for x in edges[1:]]

    data_source.data = dict(hist=hist,
                            left=edges[:-1],
                            right=edges[1:],
                            color=colors)


def update_data_source(all_values, all_group_names, data_source,
                       ligth_colors, dark_colors,
                       outliers_data_source):
    df = pd.DataFrame(dict(values=all_values, group=all_group_names))

    grupo_middle = [x.split("/")[2] for x in all_group_names]

    groups = df.groupby('group')
    q1 = groups.quantile(q=0.25)
    q2 = groups.quantile(q=0.5)
    q3 = groups.quantile(q=0.75)
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    lower = q1 - 1.5 * iqr

    # find the outliers for each category
    def outliers(group):
        cat = group.name
        return group[(group.values > upper.loc[cat]['values']) | (group.values < lower.loc[cat]['values'])]['values']

    out = groups.apply(outliers).dropna()

    # prepare outlier data for plotting, we need coordinates for every outlier.
    if not out.empty:
        outx = list(out.index.get_level_values(0))
        outx = to_datetime([x.split("/")[2] for x in outx])
        outy = list(out.values)
        outliers_data_source.data = dict(outx=outx, outy=outy)

    # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
    qmin = groups.quantile(q=0.00)
    qmax = groups.quantile(q=1.00)
    upper.values = [min([x, y]) for (x, y) in zip(list(qmax.loc[:, 'values']), upper.values)]
    lower.values = [max([x, y]) for (x, y) in zip(list(qmin.loc[:, 'values']), lower.values)]

    keys = list(groups.groups.keys())

    x_start = [x.split("/")[0] for x in keys]
    x_end = [x.split("/")[1] for x in keys]
    x_middle = [x.split("/")[2] for x in keys]

    data_source.data = dict(upper_box_top=q3.values,
                            upper_box_bottom=q2.values,
                            down_box_top=q2.values,
                            down_box_bottom=q1.values,
                            upper_line_top=upper.values,
                            upper_line_bottom=q3.values,
                            down_line_top=q1.values,
                            down_line_bottom=lower.values,
                            x_position_start=to_datetime(x_start),
                            x_position_end=to_datetime(x_end),
                            x_position_middle=to_datetime(x_middle),
                            ligth_color=ligth_colors,
                            dark_color=dark_colors
                           )


def calculate_variations_and_window(original_values, original_dates, data_source, outliers_data_source, histogram_data_source, box_size):
    result = [1.0]

    period_count = 0
    period_average = 0

    period_result = []

    current_group_values = []
    all_values = []
    all_group_names = []

    ligth_colors = []
    dark_colors = []

    for i in range(1, len(original_values)):
        previous = original_values[i - 1]
        current = original_values[i]

        if previous > 0.0:
            result.append(current / previous)
        else:
            result.append(1.0)

        if period_count < box_size:
            period_count += 1
            period_average += result[-1]
            current_group_values.append(result[-1])
        else:
            period_average = period_average / period_count

            if period_average < 1:
                current_color = RGB(256, 0, 0)
                ligth_colors.append(ligth_red)
                dark_colors.append(dark_red)
            else:
                current_color = RGB(0, 256, 0)
                ligth_colors.append(ligth_green)
                dark_colors.append(dark_green)

            start_date = original_dates[i - period_count]
            end_date = original_dates[i]
            middle_date = original_dates[i - int(period_count/2)]
            key_date = start_date + "/" + end_date + "/" + middle_date

            period_result.append([period_average, period_count, current_color])

            all_values = all_values + current_group_values
            all_group_names = all_group_names + ([key_date] * len(current_group_values))

            period_count = 1
            period_average = result[-1]
            current_group_values = [result[-1]]

    update_histogram_data_source(all_values, histogram_data_source)
    update_data_source(all_values, all_group_names, data_source, ligth_colors, dark_colors, outliers_data_source)

    return result


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################




def get_plot_and_data(plot_width, plot_height, title, halvings=[]):
    data_source = ColumnDataSource(data=dict(x=[], y=[]))

    main_plot = figure(x_axis_type="datetime",
                       title=title,
                       plot_width=plot_width, plot_height=plot_height)

    main_plot.grid.grid_line_alpha = 0.3
    main_plot.xaxis.axis_label = 'Fecha'
    main_plot.yaxis.axis_label = ""

    main_plot.line(source=data_source,
                   x="x",
                   y="y",
                   color=RGB(0, 0, 255))

    main_plot.add_tools(HoverTool(
                                tooltips=[('Fecha', '@x{%F}'),
                                          ('Valor', '@y')],
                                formatters={'@x': 'datetime'},
                                mode='vline'
                        ))

    for date in halvings:
        line = Span(location=datetime.datetime.strptime(date, "%Y-%m-%d"),
                    dimension='height', line_color='red',
                    line_dash='dashed', line_width=1)
        main_plot.add_layout(line)

    return main_plot, data_source

#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


def fix_hash_power(hash_power_df):

    new_data = []
    new_dates = []

    old_data = hash_power_df.Value.values
    old_dates = hash_power_df.Date.values

    i = 0

    while i < len(old_data):

        current_date = datetime.datetime.strptime(old_dates[i], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(old_dates[i + 1], '%Y-%m-%d')

        while current_date <= end_date:
            new_data.append(old_data[i])
            new_dates.append(current_date.strftime('%Y-%m-%d'))

            current_date = current_date + datetime.timedelta(days=1)

        i += 2

    return pd.DataFrame(dict(Date=new_dates, Value=new_data))


def calculate_bitcoin_cost(hash_power_df, hash_rate_df, electricity_cost):
    hash_power_fix_df = fix_hash_power(hash_power_df)
    result = pd.merge(hash_power_fix_df, hash_rate_df, on="Date")
    result["Value"] = result.Value_x * result.Value_y * electricity_cost

    return result[["Date", "Value"]]


##########################################################################


def get_generic_plort(title, x_axis, y_axis, y_axis_money=False, x_axis_is_date=True):

    if x_axis_is_date:
        p1 = figure(x_axis_type="datetime",
                    title=title,
                    plot_width=1000,
                    plot_height=700)
    else:
        p1 = figure(title=title,
                    plot_width=1000,
                    plot_height=700)

    p1.title.text_font_size = '15pt'

    p1.grid.grid_line_alpha = 0.4

    p1.xaxis.axis_label = x_axis
    p1.xaxis.axis_label_text_font_size = "15pt"
    p1.xaxis.major_label_text_font_size = "10pt"

    p1.yaxis.axis_label = y_axis
    p1.yaxis.axis_label_text_font_size = "15pt"
    p1.yaxis.major_label_text_font_size = "10pt"

    if y_axis_money:
        p1.yaxis.formatter = NumeralTickFormatter(format="$0,0")

    return p1

