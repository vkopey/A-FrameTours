import threading
import http.server
import socketserver
import webbrowser

PORT = 8000
message=[""] # або queue.Queue()

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # Отримати довжину даних
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        message[0]=post_data.decode("utf-8")
        print("Отримано POST:", message[0])

        # Відповідь клієнту
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("".encode("utf-8"))

# Функція запуску сервера
def start_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()

def launch_server():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start() # запуск в окремому потоці
    #webbrowser.open(f"http://localhost:{PORT}")