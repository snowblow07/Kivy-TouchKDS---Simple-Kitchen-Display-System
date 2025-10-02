import os
import shutil
import datetime
import logging
from dotenv import load_dotenv

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INPUT_DIR = os.getenv('INPUT_DIR', 'print_output')
PROCESSED_DIR = os.getenv('PROCESSED_DIR', 'processed_output')
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', 2))

# Timer color thresholds (in seconds)
COLOR_ALERT_YELLOW = int(os.getenv('COLOR_ALERT_YELLOW', 300))  # 5 minutes
COLOR_ALERT_RED = int(os.getenv('COLOR_ALERT_RED', 600))        # 10 minutes


def parse_raw_order(text_content):
    """
    Parses the raw text from a print job into a structured dictionary.

    Args:
        text_content (str): The raw text extracted from the print file.

    Returns:
        dict: A dictionary containing parsed order details (order_id, table, server, etc.).
    """
    data = {
        'order_id': 'N/A',
        'table': 'N/A',
        'server': 'N/A',
        'order_type': 'N/A',
        'items': [],
        'sent_time': datetime.datetime.now()  # Fallback to now
    }
    
    lines = text_content.split('\n')
    item_section_started = False

    for line in lines:
        clean_line = line.strip()

        # --- Extract Key-Value Information ---
        if 'Order:' in line:
            try:
                data['order_id'] = line.split('Order:')[1].split()[0]
            except IndexError:
                pass
        if 'Server:' in line:
            try:
                data['server'] = line.split('Server:')[1].strip()
            except IndexError:
                pass
        if 'Table:' in line:
            try:
                data['table'] = line.split('Table:')[1].split()[0]
            except IndexError:
                pass
        if 'Dine In' in line:
            data['order_type'] = 'Dine In'

        # --- Extract Accurate "Sent" Timestamp ---
        if 'Sent:' in line:
            try:
                time_str = line.split('Sent:')[1].strip()
                # Expected format: 07/24/2025 - 04:53:14 PM
                data['sent_time'] = datetime.datetime.strptime(time_str, '%m/%d/%Y - %I:%M:%S %p')
            except (ValueError, IndexError):
                logger.warning(f"Could not parse timestamp '{line}'. Using current time.")
        
        # --- Logic to identify and capture the items list ---
        if 'Table:' in line:
            item_section_started = True
            continue  # Move to next line
        
        if 'Sent:' in line:
            item_section_started = False
            continue  # Stop processing items

        # Valid item or modifier check
        if item_section_started and clean_line and '---' not in clean_line and '<<<' not in clean_line:
            if not clean_line[0].isdigit():
                # Indent modifiers for clarity
                data['items'].append(f"    - {clean_line}")
            else:
                data['items'].append(clean_line)

    return data


class OrderTicket(BoxLayout):
    """
    A widget that represents a single order ticket on the screen.
    Displays order headers, items, and an elapsed timer that changes color based on wait time.
    """
    def __init__(self, order_data, filename, bump_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 450
        self.padding = 10
        self.spacing = 5
        
        self.filename = filename
        self.creation_time = order_data.get('sent_time', datetime.datetime.now())

        # Set up the background color
        with self.canvas.before:
            self.bg_color = Color(0.2, 0.6, 0.2, 1)  # Start with green
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect_background, pos=self._update_rect_background)

        # --- Enhanced Header ---
        header = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=4)
        
        # Header Row 1: Order ID and Table/Type
        header_row1 = BoxLayout()
        order_label = Label(
            text=f"Order #{order_data.get('order_id')}", font_size='22sp', bold=True, 
            halign='left', valign='middle', size_hint_x=0.6
        )
        table_label = Label(
            text=f"{order_data.get('table')} ({order_data.get('order_type')})", font_size='18sp',
            halign='right', valign='middle', size_hint_x=0.4
        )
        order_label.bind(size=order_label.setter('text_size'))
        table_label.bind(size=table_label.setter('text_size'))
        header_row1.add_widget(order_label)
        header_row1.add_widget(table_label)
        
        # Header Row 2: Server and Timer
        header_row2 = BoxLayout()
        server_label = Label(
            text=f"Server: {order_data.get('server')}", font_size='16sp', color=(0.9, 0.9, 0.9, 1),
            halign='left', valign='middle', size_hint_x=0.6
        )
        self.timer_label = Label(
            text="00:00", font_size='22sp', bold=True,
            halign='right', valign='middle', size_hint_x=0.4
        )
        server_label.bind(size=server_label.setter('text_size'))
        self.timer_label.bind(size=self.timer_label.setter('text_size'))
        header_row2.add_widget(server_label)
        header_row2.add_widget(self.timer_label)

        header.add_widget(header_row1)
        header.add_widget(header_row2)
        self.add_widget(header)

        # Item List
        item_list_layout = ScrollView(size_hint_y=0.6)
        item_labels_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        item_labels_grid.bind(minimum_height=item_labels_grid.setter('height'))
        
        for item in order_data.get('items', ['No items found.']):
            item_labels_grid.add_widget(Label(
                text=item, font_size='18sp', size_hint_y=None, height=40,
                halign='left', valign='middle', padding_x=10
            ))
        
        if item_labels_grid.children:
            item_labels_grid.children[-1].bind(size=item_labels_grid.children[-1].setter('text_size'))

        item_list_layout.add_widget(item_labels_grid)
        self.add_widget(item_list_layout)

        # "Bump" Button
        bump_button = Button(
            text="Complete", font_size='20sp', size_hint_y=0.15,
            on_press=lambda x: bump_callback(self)
        )
        self.add_widget(bump_button)

    def _update_rect_background(self, instance, value):
        """Updates the background rectangle position and size when the widget changes."""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def update_timer_and_color(self):
        """Calculates elapsed time and updates the label and background color."""
        elapsed = datetime.datetime.now() - self.creation_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        self.timer_label.text = f"{minutes:02}:{seconds:02}"
        
        total_seconds = elapsed.total_seconds()
        if total_seconds > COLOR_ALERT_RED:
            self.bg_color.rgba = (0.8, 0.2, 0.2, 1)  # Red
        elif total_seconds > COLOR_ALERT_YELLOW:
            self.bg_color.rgba = (0.9, 0.7, 0.1, 1)  # Yellow


class KDSApp(App):
    """
    Main Kitchen Display System Kivy Application.
    Polls the input directory for new print jobs and renders them to the screen.
    """
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        root_layout = BoxLayout(orientation='vertical', padding=10)
        title_label = Label(
            text="KDS - Kitchen Display System", font_size='32sp', bold=True, size_hint_y=0.1
        )
        root_layout.add_widget(title_label)

        self.order_grid = GridLayout(cols=3, spacing=15, size_hint_y=None)
        self.order_grid.bind(minimum_height=self.order_grid.setter('height'))
        
        scroll_view = ScrollView(size_hint=(1, 0.9))
        scroll_view.add_widget(self.order_grid)
        root_layout.add_widget(scroll_view)

        self.active_orders = {}
        self.setup_directories()

        Clock.schedule_interval(self.check_for_new_orders, POLL_INTERVAL_SECONDS)
        Clock.schedule_interval(self.update_all_timers, 1)
        return root_layout

    def setup_directories(self):
        """Creates required input and processed directories if they don't exist."""
        for path in [INPUT_DIR, PROCESSED_DIR]:
            if not os.path.exists(path):
                os.makedirs(path)

    def check_for_new_orders(self, dt):
        """Polls the input directory for new text files to process."""
        for filename in os.listdir(INPUT_DIR):
            if filename.endswith((".txt", ".prn")) and filename not in self.active_orders:
                filepath = os.path.join(INPUT_DIR, filename)
                self.create_order_ticket(filepath, filename)

    def create_order_ticket(self, filepath, filename):
        """
        Reads the content of an order file and creates a corresponding UI widget.
        
        Args:
            filepath (str): The full path to the order file.
            filename (str): The name of the file to track it within active orders.
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            order_data = parse_raw_order(content)
            
            if not order_data['items']:
                logger.warning(f"No items found in {filename}. Skipping.")
                return

            order_widget = OrderTicket(
                order_data=order_data,
                filename=filename,
                bump_callback=self.bump_order
            )
            
            self.order_grid.add_widget(order_widget)
            self.active_orders[filename] = order_widget
            logger.info(f"New order displayed: {filename}")

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")

    def bump_order(self, order_widget):
        """
        Removes an order widget from the UI and moves the associated file to the processed directory.
        
        Args:
            order_widget (OrderTicket): The widget instance being bumped.
        """
        filename = order_widget.filename
        self.order_grid.remove_widget(order_widget)
        
        source_path = os.path.join(INPUT_DIR, filename)
        dest_path = os.path.join(PROCESSED_DIR, filename)
        
        try:
            shutil.move(source_path, dest_path)
            logger.info(f"Completed and moved {filename}")
        except Exception as e:
            logger.error(f"Could not move file {filename}: {e}")

        if filename in self.active_orders:
            del self.active_orders[filename]

    def update_all_timers(self, dt):
        """Iterates over all active orders to update their visual timers."""
        for widget in self.active_orders.values():
            widget.update_timer_and_color()

if __name__ == "__main__":
    KDSApp().run()
