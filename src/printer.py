import socket
import threading
import os
import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration from environment variables
HOST = os.getenv('PRINTER_HOST', '0.0.0.0')
PORT = int(os.getenv('PRINTER_PORT', 9100))
OUTPUT_DIR = os.getenv('INPUT_DIR', 'print_output')

def handle_client(client_socket, client_address):
    """
    Handles an incoming client connection, receives data, and saves it to a file.
    
    Args:
        client_socket (socket.socket): The connected client socket.
        client_address (tuple): The IP address and port of the client.
    """
    logger.info(f"Accepted connection from: {client_address[0]}:{client_address[1]}")

    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            logger.info(f"Created output directory: {OUTPUT_DIR}")

        # Generate a unique filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_filename = os.path.join(OUTPUT_DIR, f"print_job_{timestamp}.txt")

        with open(output_filename, 'wb') as f:
            while True:
                data = client_socket.recv(4096)  # Read data in chunks
                if not data:
                    break  # No more data from client
                f.write(data)
                
        logger.info(f"Print job saved to: {output_filename}")

    except Exception as e:
        logger.error(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Connection closed for: {client_address[0]}:{client_address[1]}")

def start_printer_server():
    """
    Starts the TCP server to listen for print jobs on the configured host and port.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reusing the address
    server.bind((HOST, PORT))
    server.listen(5)  # Max 5 pending connections

    logger.info(f"Listening on {HOST}:{PORT}")
    logger.info(f"Print jobs will be saved to the '{OUTPUT_DIR}' directory.")
    logger.info("To stop the server, press Ctrl+C.")

    while True:
        try:
            client_socket, address = server.accept()
            # Handle client connection in a new thread
            client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
            client_handler.start()
        except KeyboardInterrupt:
            logger.info("\nShutting down server...")
            server.close()
            break
        except Exception as e:
            logger.error(f"Server error: {e}")

if __name__ == "__main__":
    start_printer_server()
