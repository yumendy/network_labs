import SocketServer
import math
import os
import random

from protocol.msg_protocol import MsgHeader, StructManagement, get_max_payload_size, DataPacket

LOSE_PACKET_NUM_PER_100_PACKET = 5


class SampleGBNThreadedUDPServer(SocketServer.UDPServer):
    pass


class GBNHandler(SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.ack_seq = -1
        self.window_size = 10
        self.max_seq = 0
        self.data_packet_list = self.get_data_packet_list()
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        first_packet_data = self.request[0]
        address, port = self.client_address
        header = MsgHeader.from_bytes(first_packet_data)
        if StructManagement.verify_msg_header(header):
            if header.msg_type == 0x01:
                print 'received a request packet with from %s %s' % self.client_address
                self.deliver_data()
            elif header.msg_type == 0x03:
                seq = header.seq
                print 'received a ack packet with seq %d' % seq
                if seq > self.ack_seq:
                    self.ack_seq = seq
                self.deliver_data()
            else:
                print 'received a packet with unexpected msg_type %d form %s port %s!' % (
                    header.msg_type, address, port)
        else:
            print 'received a packet with unexpected magic_type %d form %s port %s!' % (
                header.magic_type, address, port)

    def deliver_data(self):
        client = self.request[1]
        if self.ack_seq == self.max_seq - 1:
            client.sendto(self.gen_finish_packet().to_bytes(), self.client_address)
        else:
            last = min(self.ack_seq + 1 + self.window_size, self.max_seq)
            for idx in xrange(self.ack_seq + 1, last):
                if random.randint(1, 100) > LOSE_PACKET_NUM_PER_100_PACKET:
                    client.sendto(self.data_packet_list[idx].to_bytes(), self.client_address)
                    print "send a data packet with seq %d" % idx
                else:
                    print "lost data packet with seq %d" % idx

    def get_data_packet_list(self):
        with open('1.mp3', 'rb') as fp:
            max_size = get_max_payload_size()
            fp.seek(-1, os.SEEK_END)
            content_len = fp.tell()
            fp.seek(0, os.SEEK_SET)
            self.max_seq = int(math.ceil(content_len * 1.0 / max_size))
            data_packet_list = [self.gen_data_packet(seq, fp.read(max_size)) for seq in xrange(self.max_seq)]
        return data_packet_list

    def gen_data_packet(self, seq, content):
        return DataPacket(StructManagement.gen_msg_header(0x02, seq, len(content)), content)

    def gen_finish_packet(self):
        return DataPacket(StructManagement.gen_msg_header(0x04, 0, 0), '')


if __name__ == '__main__':
    HOST, PORT = "localhost", 8888
    server = SocketServer.UDPServer((HOST, PORT), GBNHandler)
    server.serve_forever()
