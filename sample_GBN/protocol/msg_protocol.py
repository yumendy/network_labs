import struct


class CStruct(object):
    format = ''
    attr_tuple = tuple()

    def __init__(self, *args):
        self.__dict__ = dict(zip(self.attr_tuple, args))

    @classmethod
    def from_bytes(cls, bytes_array):
        s = struct.Struct(cls.format)
        return cls(*s.unpack(bytes_array))

    def to_bytes(self):
        s = struct.Struct(self.format)
        return s.pack(*map(lambda x: getattr(self, x), self.attr_tuple))


class MsgHeader(CStruct):
    """
    msg_header_t {
        UINT16 magic_number; 2B
        UINT8 version; 2B
        UINT8 msg_type; 2B
        UINT16 cont_len; 2B
        UINT64 seq; 8B
    } 16B
    
    magic_number : 0x0209
    version : 0x01
    msg_type : 0x01 - content request msg; 0x02 - data msg; 0x03 - ack msg; 0x04 -finish;
    """
    format = "HHHHQ"
    attr_tuple = ('magic_number', 'version', 'msg_type', 'cont_len', 'seq')


class DataPacket(object):
    def __init__(self, msg_header, payload):
        self.msg_header = msg_header
        self.payload = payload

    @classmethod
    def from_bytes(cls, bytes_array):
        header = bytes_array[:struct.calcsize(MsgHeader.format)]
        payload = bytes_array[struct.calcsize(MsgHeader.format):]
        return cls(MsgHeader.from_bytes(header), payload)

    def to_bytes(self):
        return self.msg_header.to_bytes() + self.payload


class StructManagement(object):
    @staticmethod
    def gen_msg_header(msg_type, seq, cont_len):
        return MsgHeader(0x0209, 0x01, msg_type, cont_len, seq)

    @staticmethod
    def verify_msg_header(msg_header):
        return msg_header.magic_number == 0x0209 and msg_header.version == 0x01


def get_max_payload_size():
    return 1472 - struct.calcsize(MsgHeader.format)
