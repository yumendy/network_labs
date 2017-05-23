#include <iostream>
//#include <rpcndr.h>
#include <windef.h>
#include <afxres.h>

#define STUD_IP_TEST_CORRECT 0
#define STUD_IP_TEST_CHECKSUM_ERROR 1
#define STUD_IP_TEST_TTL_ERROR 2
#define STUD_IP_TEST_VERSION_ERROR 3
#define STUD_IP_TEST_HEADLEN_ERROR 4
#define STUD_IP_TEST_DESTINATION_ERROR 5

using namespace std;

/*
* THIS FILE IS FOR IP TEST
*/
// system support

extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer, int length);

extern unsigned int getIpv4Address();

#pragma pack(push)
#pragma pack(1)

typedef struct _header {
    UINT8 IHL: 4;
    UINT8 version: 4;

    UINT8 ecn : 2;
    UINT8 type_of_service: 6;

    UINT16 total_length;

    UINT16 identifilcation;

    UINT16 offset:13;
    UINT16 MF:1;
    UINT16 DF:1;
    UINT16 reserved:1;

    UINT8 ttl;
    UINT8 protocol;
    UINT16 checksum;
    UINT32 source_address;
    UINT32 destination_address;
    BYTE options[0];
} Header;

#pragma pack(pop)


// implemented by students

bool check_version(Header* header) {
    return header->version == 4;
}

bool check_header_length(Header *header) {
    return header->IHL >= 5 && header->IHL <= 16;
}

bool check_ttl(Header *header) {
    return header->ttl > 1;
}

UINT16 calc_checksum(Header *header) {
    unsigned int ihl = header->IHL;
    UINT32 checksum = 0;
    for (int i = 0; i < ihl * 2; ++i) {
        UINT16 temp = 0;
        temp += *((unsigned char*)header + (i * 2)) << 8;
        temp += *((unsigned char*)header + (i * 2 + 1));
        checksum += temp;
    }
    UINT16 result = 0;
    result += *((UINT16 *) &checksum);
    result += *(((UINT16 *) &checksum) + 1);
    return ~result;
}

bool check_checksum(Header* header) {
    return calc_checksum(header) == 0x0000;
}


bool check_destination(Header* header) {
    UINT32 address = ntohl(header->destination_address);
    return address == getIpv4Address() || address == 0xffffffff;
};

int stud_ip_recv(char *pBuffer,unsigned short length)
{
    Header* header = (Header*)pBuffer;

    // check version
    if (!check_version(header)) {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR);
        return 1;
    }

    // check header length
    if (!check_header_length(header)) {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR);
        return 1;
    }

    // check ttl
    if (!check_ttl(header)) {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR);
        return 1;
    }

    // check checksum
    if (!check_checksum(header)) {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);
        return 1;
    }

    // check destination
    if (!check_destination(header)) {
        ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);
        return 1;
    }

    // send to up
    ip_SendtoUp(pBuffer, length);
    return 0;
}

int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
                   unsigned int dstAddr,byte protocol,byte ttl)
{
    char* buffer = new char[sizeof(Header) + len];
    memcpy(buffer + sizeof(Header), pBuffer, len);
    Header header;
    memset(&header, 0, sizeof(Header));
    header.version = 4;
    header.IHL = 5;
    header.ttl = ttl;
    header.protocol = protocol;
    header.total_length = htons(sizeof(Header) + len);
    header.source_address = htonl(srcAddr);
    header.destination_address = htonl(dstAddr);

    header.checksum = htons(calc_checksum(&header));

    memcpy(buffer, &header, sizeof(Header));
    ip_SendtoLower(buffer, sizeof(Header) + len);

    return 0;
}

int main() {
    return 0;
}
