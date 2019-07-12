from subprocess import check_output
from xml.etree.ElementTree import fromstring
import math
from functools import reduce


def subnet_calculator(*args):
    # if no address provided
    if len(args) == 0:
        address = get_local_address()
    else:
        address = args[0]
        # validate
        if not validate(address):
            return

    # net address
    net_address = get_net_address(address)
    print(f'Net address binary: {net_address["bin"]}')
    print(f'Net address decimal: {net_address["dec"]}')

    # net class
    net_class = get_net_class(net_address["bin"])
    print(f'Net class: {net_class}')

    # net mask
    mask_short = int(address.split('/')[1])
    net_mask = get_net_mask(mask_short)
    print(f'Net mask binary: {net_mask["bin"]}')
    print(f'Net mask decimal: {net_mask["dec"]}')

    # broadcast address
    broadcast_address = get_broadcast_address(address)
    print(f'Broadcast address binary: {broadcast_address["bin"]}')
    print(f'Broadcast address decimal: {broadcast_address["dec"]}')

    # min host address
    min_host = get_min_host(net_address["bin"], mask_short)
    print(f'Min host address binary: {min_host["bin"]}')
    print(f'Min host address decimal: {min_host["dec"]}')

    # max host address
    max_host = get_max_host(broadcast_address["bin"])
    print(f'Max host address binary: {max_host["bin"]}')
    print(f'Max host address decimal: {max_host["dec"]}')

    # hosts number
    hosts_number = get_hosts_number(net_mask['bin'])
    print(f'Hosts number: {hosts_number}')


def get_local_address():
    # run wmic and output ipaddress and IPSubnet in xml
    cmd = 'wmic.exe nicconfig where "IPEnabled  = True" get ipaddress,IPSubnet /format:rawxml'
    xml_text = check_output(cmd, creationflags=8)
    xml_root = fromstring(xml_text)
    # take first instance
    first_instance = xml_root.find("./RESULTS/CIM/INSTANCE")
    first_ip = first_instance[0].find(
        "./VALUE.ARRAY/VALUE").text  # first value is the ip
    first_mask = first_instance[1].find(
        "./VALUE.ARRAY/VALUE").text  # first value is the mask
    # convert mask to binary
    mask_bin = [dec2binary(int(part), 8) for part in first_mask.split('.')]
    # count 1s
    mask_short = '.'.join(mask_bin).count('1')

    return f'{first_ip}/{mask_short}'


def validate(address):
    ip = address.split('/')
    addres_correct = True
    # check address validity
    ip_parts = ip[0].split('.')
    for part in ip_parts:
        if not part.isnumeric():
            print('Addres is not composed of only numbers and dots')
            addres_correct = False
        else:
            if not(int(part) >= 0 and int(part) <= 255):
                print('Not all parts of the address are within [0:255] range')
                addres_correct = False
    if len(ip_parts) != 4:
        print('The number of address parts is different than 4')
        addres_correct = False
    if int(ip[1]) < 0 or int(ip[1]) > 32:
        print('The mask is not within [0:31] range')
        addres_correct = False
    return addres_correct


def dec2binary(num, length):
    queue = []
    while num != 0:
        queue.insert(0, num % 2)
        num = num // 2
    return f'{"".join(str(i) for i in queue):0>{length}}'


def get_net_address(address):
    # list of octets
    ip_dec_list = [int(part) for part in address.split('/')[0].split('.')]
    mask_short = int(address.split('/')[1])
    # determine how many bytes are reserved for net address, rest is for host
    net_bytes = mask_short % 8
    # determine which octet does the mask point to
    octet_number = math.ceil(mask_short / 8)
    # octet binary value
    octet_bin = dec2binary(int(ip_dec_list[octet_number - 1]), 8)
    # calculate the net_address binary value
    octet_net_part_bin = f'{octet_bin[:net_bytes]:0<8}'
    octet_net_part_dec = int(octet_net_part_bin, 2)
    # clone ip
    net_address = list(ip_dec_list)
    # swap host octets
    net_address[octet_number-1] = octet_net_part_dec
    for i in range(octet_number, 4):
        net_address[i] = 0
    return {
        'bin': '.'.join([dec2binary(part, 8) for part in net_address]),
        'dec': '.'.join(str(part) for part in net_address)
    }


def get_net_class(net_address_bin):
    first_octet = net_address_bin.split('.')[0]
    if first_octet[0] == '0':
        return 'A'
    elif first_octet[0:2] == '01':
        return 'B'
    elif first_octet[0:3] == '110':
        return 'C'
    elif first_octet[0:4] == '1110':
        return 'D'
    elif first_octet[0:4] == '1111':
        return 'E'


def get_net_mask(net_mask_short):
    mask_bin = f'{net_mask_short * "1":0<32}'
    mask_bin = [f'{mask_bin[0:8]:s}', f'{mask_bin[8:16]:s}',
                f'{mask_bin[16:24]:s}', f'{mask_bin[24:32]:s}']
    mask_dec = [int(part, 2) for part in mask_bin]
    return {
        'bin': '.'.join(mask_bin),
        'dec': '.'.join(str(part) for part in mask_dec)
    }


def get_broadcast_address(address):
    # list of octets
    ip_dec_list = [int(part) for part in address.split('/')[0].split('.')]
    mask_short = int(address.split('/')[1])
    # determine how many bytes are reserved for net address, rest is for host
    net_bytes = mask_short % 8
    # determine which octet does the mask point to
    octet_number = math.ceil(mask_short / 8)
    # octet binary value
    octet_bin = dec2binary(int(ip_dec_list[octet_number - 1]), 8)
    # calculate the net_address binary value
    octet_net_part_bin = f'{octet_bin[:net_bytes]:1<8}'
    octet_net_part_dec = int(octet_net_part_bin, 2)
    # clone ip
    broadcast_address = list(ip_dec_list)
    # swap host octets
    broadcast_address[octet_number-1] = octet_net_part_dec
    for i in range(octet_number, 4):
        broadcast_address[i] = 255
    return {
        'bin': '.'.join([dec2binary(part, 8) for part in broadcast_address]),
        'dec': '.'.join(str(part) for part in broadcast_address)
    }


def get_min_host(net_address_bin, mask_short):
    min_host_bin = f'{net_address_bin.replace(".","")[:mask_short + 1]:0<32}'
    min_host_bin = [min_host_bin[0:8], min_host_bin[8:16],
                    min_host_bin[16:24], dec2binary(int(min_host_bin[24:32]) + 1, 8)]
    min_host_dec = [int(part, 2) for part in min_host_bin]
    return {
        'bin': '.'.join(min_host_bin),
        'dec': '.'.join(str(part) for part in min_host_dec)
    }


def get_max_host(broadcast_address_bin):
    last_octet = broadcast_address_bin[-8:]
    max_host_bin = broadcast_address_bin[:-8] + dec2binary(int(last_octet, 2)-1, 8)
    max_host_dec = [int(part, 2) for part in max_host_bin.split('.')]
    return {
        'bin': max_host_bin,
        'dec': '.'.join(str(part) for part in max_host_dec)
    }


def get_hosts_number(mask_bin):
    return 2 ** mask_bin.count('0') - 2


# address format: 111.222.333.444/16
subnet_calculator()  # '11.130.13.14/12')
