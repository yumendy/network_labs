import SocketServer
import datetime
import select
import socket
import urlparse


class IPTables(object):
    __ip_tables = None

    def __init__(self):
        self.black_list = {}
        self.block_user = {'127.0.0.1'}
        self.white_list = {}
        self.redirect_list = {'today.hit.edu.cn': 'www.hit.edu.cn'}

    def get_black_list(self):
        return self.black_list

    def get_block_user_list(self):
        return self.block_user

    def get_redirect_list(self):
        return self.redirect_list

    @staticmethod
    def get_instance():
        if IPTables.__ip_tables is None:
            IPTables.__ip_tables = IPTables()
        return IPTables.__ip_tables

    def __new__(cls, *args, **kwargs):
        if IPTables.__ip_tables is None:
            IPTables.__ip_tables = super(IPTables, cls).__new__(cls)
        return IPTables.__ip_tables


class ConnectionHandler(SocketServer.BaseRequestHandler):
    def read_line(self):
        data_buffer = []
        while True:
            ch = self.request.recv(1)
            if ch == '\n':
                break
            else:
                data_buffer.append(ch)
        return ''.join(data_buffer)

    def read_line_by_buffer(self):
        self.data_buffer = ''
        while True:
            self.data_buffer += self.request.recv(8192)
            end_index = self.data_buffer.find('\n')
            if end_index != -1:
                break
        result = self.data_buffer[:end_index + 1]
        self.data_buffer = self.data_buffer[end_index + 1:]
        return result

    def handle(self):
        self.parse_first_line(self.read_line_by_buffer())
        if self.block_check():
            self.request.close()
            return None

        # TODO: jump
        self.redirect_check()

        if self.method == 'CONNECT':
            self.connect_method_handler()
        else:
            self.other_method_handler()
        self.request.close()
        self.target.close()

    def block_check(self):
        if self.url.hostname in IPTables.get_instance().get_black_list():
            self.send_block_response()
            self.request.close()
            return True
        elif self.client_address[0] in IPTables.get_instance().get_block_user_list():
            self.send_block_response()
            self.request.close()
            return True
        else:
            return False

    def redirect_check(self):
        if self.url.hostname in IPTables.get_instance().get_redirect_list():
            self.target_url = IPTables.get_instance().get_redirect_list()[self.url.hostname]
            self.target_port = 80
            self.method = 'GET'
        else:
            if not self.url.hostname:
                self.target_url, self.target_port = tuple(self.url.path.split(':'))
                self.target_port = int(self.target_port)
            else:
                self.target_url = self.url.hostname
                self.target_port = 80 if not self.url.port else int(self.url.port)
        return True

    def connect_method_handler(self):
        self.connect()
        self.request.send('HTTP/1.1 200 Connection established\nProxy-agent: Python proxy/1.0\n\n')
        self.data_transmission()

    def other_method_handler(self):
        self.connect()
        self.target.send("%s %s %s\n" % (self.method, self.url.path, self.version) + self.data_buffer)
        self.data_transmission()

    def data_transmission(self):
        socket_list = [self.request, self.target]
        time_out_counter = 0
        while time_out_counter < 5:
            time_out_counter += 1
            r, w, x = select.select(socket_list, [], socket_list, 3)
            if x:
                break
            if r:
                for readable_socket in r:
                    try:
                        data = readable_socket.recv(8192)
                    except Exception as e:
                        print e
                        data = ''
                    send_to = self.target if readable_socket is self.request else self.request
                    if data:
                        send_to.send(data)
                        time_out_counter = 0

    def connect(self):

        self.target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print self.target_url, self.target_port
        self.target.connect((self.target_url, self.target_port))

    def send_block_response(self):
        request_template = 'HTTP/1.1 404 Not Found\r\nDate: %s GMT\r\nContent-Type: ' \
                           'text/html;charset=ISO-8859-1\r\nContent-Length: 104\r\n\r\n<html><head><title>404 Not ' \
                           'Found</title></head><body>404 Not Found.<!-- body goes here --></body></html>'
        response_data = request_template % datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S')
        self.request.send(response_data)

    def parse_first_line(self, line):
        data_list = line.split()
        self.method = data_list[0].upper()
        self.url = urlparse.urlsplit(data_list[1])
        self.version = data_list[2]


class Proxy(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


if __name__ == '__main__':
    proxy = Proxy(('localhost', 8888), ConnectionHandler)
    proxy.serve_forever()
