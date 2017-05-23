#include <iostream>
#include <vector>
#include <basetsd.h>
#include <afxres.h>

using namespace std;
/*
* THIS FILE IS FOR IP FORWARD TEST
*/

# define STUD_FORWARD_TEST_TTLERROR 1
# define STUD_FORWARD_TEST_NOROUTE 2

typedef struct stud_route_msg {
    unsigned int dest;
    unsigned int masklen;
    unsigned int nexthop;
} stud_route_msg;


// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students

vector<stud_route_msg> route_table;


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

void stud_Route_Init()
{
    route_table.clear();
    return;
}

void stud_route_add(stud_route_msg *proute)
{
    stud_route_msg route_msg;
    route_msg.masklen = ntohl(proute->masklen);
    route_msg.nexthop = ntohl(proute->nexthop);
    route_msg.dest = ntohl(proute->dest) & 0xffffffff << (32 - route_msg.masklen);
    route_table.push_back(route_msg);
    return;
}

stud_route_msg* find_route_path(unsigned int ip) {
    stud_route_msg* result = NULL;
    unsigned int max_mask_length = 0;

    for (int i = 0; i < route_table.size(); ++i) {
        stud_route_msg route = route_table[i];
        unsigned int route_network_num = route.dest;
        unsigned int ip_network_num = ip & (0xffffffff << (32 - route.masklen));
        if (route_network_num == ip_network_num && route.masklen > max_mask_length) {
            result = &(route_table[i]);
            max_mask_length = route.masklen;
        }
    }
    return result;
}


int stud_fwd_deal(char *pBuffer, int length)
{
    Header* header = (Header*)pBuffer;

    // check if packet for route
    if (ntohl(header->destination_address) == getIpv4Address()) {
        fwd_LocalRcv(pBuffer, length);
        return 0;
    }

    // find route path

    stud_route_msg* route_msg = find_route_path(ntohl(header->destination_address));
    if (!route_msg) {
        fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
        return 1;
    } else {
        if (!check_ttl(header)) {
            fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
            return 1;
        } else {
            header->ttl--;
            header->checksum = 0x0000;
            header->checksum = htons(calc_checksum(header));
            fwd_SendtoLower(pBuffer, length, route_msg->nexthop);
        }
    }

    return 0;
}





int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}