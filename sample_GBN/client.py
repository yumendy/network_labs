import random
import socket

from protocol.msg_protocol import StructManagement, DataPacket

LOSE_PACKET_NUM_PER_100_PACKET = 5


class BGNClient(object):
    def __init__(self, host, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(0.5)
        self.host = host
        self.port = port
        self.receive_fp = open('2.mp3', 'wb')
        self.expected_seq = 0

    def __del__(self):
        self.receive_fp.close()

    def send_request_packet(self):
        request_header = StructManagement.gen_msg_header(0x01, 0, 0)
        self.client_socket.sendto(request_header.to_bytes(), (self.host, self.port))

    def receive_data(self):
        try:
            data, server_address = self.client_socket.recvfrom(2048)
        except socket.timeout:
            return -1
        else:
            data_packet = DataPacket.from_bytes(data)
            if StructManagement.verify_msg_header(data_packet.msg_header):
                if data_packet.msg_header.msg_type == 0x02:
                    if data_packet.msg_header.seq == self.expected_seq:
                        self.receive_fp.write(data_packet.payload[:data_packet.msg_header.cont_len])
                        self.expected_seq += 1
                        return 0
                    else:
                        print "received a packet with seq %d, but expect seq %d." % (
                            data_packet.msg_header.seq, self.expected_seq)
                elif data_packet.msg_header.msg_type == 0x04:
                    print "received finished!"
                    return 1
                else:
                    print "received an unexpected packet with type %d" % data_packet.msg_header.msg_type
            else:
                print "received an unexpected packet"
            return -2

    def send_ack_packet(self):
        ack_header = StructManagement.gen_msg_header(0x03, self.expected_seq - 1, 0)
        data_packet = DataPacket(ack_header, '')
        self.client_socket.sendto(data_packet.to_bytes(), (self.host, self.port))
        print 'Send an ack packet to server with seq %d' % (self.expected_seq - 1)

    def run(self):
        self.send_request_packet()
        state = 0
        while True:
            while not state:
                state = self.receive_data()
            if state == 1:
                break
            elif state == -1:
                if self.expected_seq == 0:
                    self.send_request_packet()
                else:
                    if random.randint(1, 100) > LOSE_PACKET_NUM_PER_100_PACKET:
                        self.send_ack_packet()
                        state = 0
                    else:
                        print "lost ack packet of %d" % (self.expected_seq - 1)
                        state = 0
            elif state == -2:
                state = 0


if __name__ == '__main__':
    client = BGNClient('127.0.0.1', 8888)
    client.run()
