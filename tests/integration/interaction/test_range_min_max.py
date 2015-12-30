from __future__ import absolute_import

from bokeh.io import save
from bokeh.plotting import figure
from bokeh.models import CustomJS, Range1d, DataRange1d
from selenium.webdriver.common.action_chains import ActionChains

import pytest
pytestmark = pytest.mark.integration


def make_pan_plot_with_callback(xr=None, yr=None):
    if xr is None:
        x_range = Range1d(0, 3, bounds=None)
    else:
        x_range = xr
    x_callback = CustomJS(args=dict(x_range=x_range), code="""
        window.get_x_range_start = function() {
            return x_range.get('start');
        }
        window.get_x_range_end = function() {
            return x_range.get('end');
        }
    """)
    x_range.callback = x_callback

    if yr is None:
        y_range = Range1d(0, 3, bounds=None)
    else:
        y_range = yr
    y_callback = CustomJS(args=dict(y_range=y_range), code="""
        window.get_y_range_start = function() {
            return y_range.get('start');
        }
        window.get_y_range_end = function() {
            return y_range.get('end');
        }
    """)
    y_range.callback = y_callback

    plot = figure(
        height=400, width=400, tools='pan,box_zoom,reset', x_range=x_range, y_range=y_range
    )
    plot.min_border = 0
    plot.rect(x=[1, 2], y=[1, 1], width=0.9, height=0.9)
    return plot


def pan_plot(selenium, pan_x=None, pan_y=None):
    # Enable the pan tool
    pan_buttons = selenium.find_elements_by_css_selector('.bk-button-bar-list[type="pan"] button')
    pan_button = pan_buttons[0]
    if 'active' not in pan_button.get_attribute('class'):
        pan_button.click()

    canvas = selenium.find_element_by_tag_name('canvas')
    actions = ActionChains(selenium)
    actions.move_to_element_with_offset(canvas, 200, 200)
    actions.click_and_hold()
    actions.move_by_offset(pan_x, pan_y)
    actions.release()
    actions.perform()


def zoom_plot(selenium):
    # Enable the box zoom tool
    pan_buttons = selenium.find_elements_by_css_selector('.bk-button-bar-list[type="pan"] button')
    zoom_button = pan_buttons[1]
    if 'active' not in zoom_button.get_attribute('class'):
        zoom_button.click()

    canvas = selenium.find_element_by_tag_name('canvas')
    actions = ActionChains(selenium)
    actions.move_to_element_with_offset(canvas, 10, 10)
    actions.click_and_hold()
    actions.move_by_offset(200, 200)
    actions.release()
    actions.perform()


def test_range_with_callback_triggers_alert(output_file_url, selenium):
    # Simple test to ensure range callbacks are working
    # Rest of tests in this file depend on range callback.

    plot = make_pan_plot_with_callback()
    initial_start = plot.x_range.start
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=100, pan_y=100)
    new_range_start = float(selenium.execute_script("""alert(window.get_x_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert new_range_start < initial_start


def test_x_range_does_not_pan_left_of_x_min(output_file_url, selenium):
    x_range_min = -1
    plot = make_pan_plot_with_callback(xr=Range1d(0, 3, bounds=(x_range_min, None)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=200, pan_y=0)
    new_range_start = float(selenium.execute_script("""alert(window.get_x_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert int(new_range_start) == x_range_min


def test_x_range_does_not_pan_right_of_x_max(output_file_url, selenium):
    x_range_max = 4
    plot = make_pan_plot_with_callback(xr=Range1d(0, 3, bounds=(None, x_range_max)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=-200, pan_y=0)
    new_range_end = float(selenium.execute_script("""alert(window.get_x_range_end())"""))
    selenium.switch_to_alert().dismiss()  # This is not necessary but assists debugging
    assert int(new_range_end) == x_range_max


def test_y_range_does_not_pan_below_y_min(output_file_url, selenium):
    y_range_min = -1
    plot = make_pan_plot_with_callback(yr=Range1d(0, 3, bounds=(y_range_min, None)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=50, pan_y=-150)
    new_range_start = float(selenium.execute_script("""alert(window.get_y_range_start())"""))
    selenium.switch_to_alert().dismiss()  # This is not necessary but assists debugging
    assert int(new_range_start) == y_range_min


def test_y_range_does_not_pan_above_y_max(output_file_url, selenium):
    y_range_max = 4
    plot = make_pan_plot_with_callback(yr=Range1d(0, 3, bounds=(None, y_range_max)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=50, pan_y=150)
    new_range_end = float(selenium.execute_script("""alert(window.get_y_range_end())"""))
    selenium.switch_to_alert().dismiss()  # This is not necessary but assists debugging
    assert int(new_range_end) == y_range_max


############################
# Test reversed ranges
############################

def test_reversed_x_range_does_not_pan_right_of_x_min(output_file_url, selenium):
    x_range_min = -1
    plot = make_pan_plot_with_callback(xr=Range1d(3, 0, bounds=(x_range_min, None)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=-200, pan_y=0)
    new_range_start = float(selenium.execute_script("""alert(window.get_x_range_end())"""))
    selenium.switch_to_alert().dismiss()
    assert int(new_range_start) == x_range_min


def test_reversed_x_range_does_not_pan_left_of_x_max(output_file_url, selenium):
    x_range_max = 4
    plot = make_pan_plot_with_callback(xr=Range1d(3, 0, bounds=(None, x_range_max)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=200, pan_y=0)
    new_range_end = float(selenium.execute_script("""alert(window.get_x_range_start())"""))
    selenium.switch_to_alert().dismiss()  # This is not necessary but assists debugging
    assert int(new_range_end) == x_range_max


def test_reversed_y_range_does_not_pan_above_y_min(output_file_url, selenium):
    y_range_min = -1
    plot = make_pan_plot_with_callback(yr=Range1d(3, 0, bounds=(y_range_min, None)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=50, pan_y=150)

    new_range_start = float(selenium.execute_script("""alert(window.get_y_range_end())"""))
    selenium.switch_to_alert().dismiss()
    assert int(new_range_start) == y_range_min


def test_reversed_y_range_does_not_pan_below_y_max(output_file_url, selenium):
    y_range_max = 4
    plot = make_pan_plot_with_callback(yr=Range1d(3, 0, bounds=(None, y_range_max)))
    save(plot)
    selenium.get(output_file_url)

    # Pan plot and test for new range value
    pan_plot(selenium, pan_x=50, pan_y=-150)
    new_range_end = float(selenium.execute_script("""alert(window.get_y_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert int(new_range_end) == y_range_max


############################
# Test auto bounds
############################

def _assert_autorange_prevents_panning_but_can_zoom(output_file_url, selenium):
    selenium.get(output_file_url)

    # Zoom into plot so we can pan around a little
    zoom_plot(selenium)

    # Now the plot is zoomed in, try a little to the right
    pan_plot(selenium, pan_x=-50, pan_y=0)
    x_range_start = float(selenium.execute_script("""alert(window.get_x_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert x_range_start > 0.5

    # Now try panning far to left to check bounds
    pan_plot(selenium, pan_x=500, pan_y=0)
    x_range_start = float(selenium.execute_script("""alert(window.get_x_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert x_range_start > 0.4
    assert x_range_start < 0.5


def test_autorange_prevents_panning_but_can_zoom_in_with_datarange1d(output_file_url, selenium):
    plot = make_pan_plot_with_callback(xr=DataRange1d(), yr=DataRange1d())
    save(plot)
    _assert_autorange_prevents_panning_but_can_zoom(output_file_url, selenium)


def test_autorange_prevents_panning_but_can_zoom_in_with_range1d(output_file_url, selenium):
    plot = make_pan_plot_with_callback(xr=Range1d(0.45, 3), yr=DataRange1d(0, 3))
    save(plot)
    _assert_autorange_prevents_panning_but_can_zoom(output_file_url, selenium)


############################
# Test no bounds
############################

def _assert_no_bounds_allows_unlimited_panning(output_file_url, selenium):
    selenium.get(output_file_url)

    pan_plot(selenium, pan_x=-5000, pan_y=15000)

    x_range_start = float(selenium.execute_script("""alert(window.get_x_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert x_range_start > 20

    y_range_start = float(selenium.execute_script("""alert(window.get_y_range_start())"""))
    selenium.switch_to_alert().dismiss()
    assert y_range_start > 20


def test_no_bounds_allows_unlimited_panning_with_datarange1d(output_file_url, selenium):
    plot = make_pan_plot_with_callback(xr=DataRange1d(bounds=None), yr=DataRange1d(bounds=None))
    save(plot)
    _assert_no_bounds_allows_unlimited_panning(output_file_url, selenium)


def test_no_bounds_allows_unlimited_panning_with_range1d(output_file_url, selenium):
    plot = make_pan_plot_with_callback(xr=Range1d(0.45, 3, bounds=None), yr=DataRange1d(0, 3, bounds=None))
    save(plot)
    _assert_no_bounds_allows_unlimited_panning(output_file_url, selenium)
