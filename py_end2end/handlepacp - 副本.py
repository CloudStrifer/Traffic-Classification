# This pyscript can directly convert pcap files to bins which size is TRIMED_FILE_LEN.
# This pyscript may take a long time to run, please wait patiently.
# Author: yanhui wu
# Time: 2020/12/14

from scapy.all import *

import os
import math
import numpy as np
from tqdm import tqdm

# The number of packet read from the pcap file by pcapreader at a time.
ONCE_READ_COUNT = 50000

# Quantity required for each pcap.
FILE_COUNT = 1000

# Uniform length of traffic.
TRIMED_FILE_LEN = 784

# The number of pakcet that should be read when handling a single session.
# Only the first TRIMED_FILE_LEN bytes are required, so do not need to read all the packets in the session.
SESSION_PACKET_COUNT = math.ceil(TRIMED_FILE_LEN / 50)

# Proportion of training sets.
TRAIN_RATIO = 0.9

# youtubeHTML5_1, torFacebook, torGoogle, torTwitter related to browers.
CLS_DICT = {"Email": ["email1a", "email1b", "email2a", "email2b"],
            "VPN-Email": ["vpn_email2b", "vpn_email2a"],
            "Chat": ["AIMchat1", "AIMchat2", "aim_chat_3a", "aim_chat_3b", "facebookchat1", "facebookchat2",
                     "facebookchat3", "facebook_chat_4a", "facebook_chat_4b", "gmailchat1", "gmailchat2", "gmailchat3",
                     "hangouts_chat_4a", "hangout_chat_4b", "ICQchat1", "ICQchat2", "icq_chat_3a", "icq_chat_3b",
                     "skype_chat1a", "skype_chat1b"],
            "VPN-Chat": ["vpn_skype_chat1b", "vpn_skype_chat1a", "vpn_icq_chat1b", "vpn_icq_chat1a",
                         "vpn_hangouts_chat1b", "vpn_hangouts_chat1a", "vpn_facebook_chat1b", "vpn_facebook_chat1a",
                         "vpn_aim_chat1b", "vpn_aim_chat1a"],
            "Streaming": ["facebook_video1a", "facebook_video1b", "facebook_video2a", "facebook_video2b",
                          "hangouts_video1b", "hangouts_video2a", "hangouts_video2b", "netflix1", "netflix2",
                          "netflix3", "netflix4", "skype_video1a", "skype_video1b", "skype_video2a", "skype_video2b",
                          "spotify1", "spotify2", "spotify3", "spotify4", "youtube1", "youtube2", "youtube3",
                          "youtube4", "youtube5", "youtube6", "vimeo3", "vimeo4", "vimeo2", "vimeo1"],
            "VPN-Streaming": ["vpn_youtube_A", "vpn_vimeo_B", "vpn_vimeo_A", "vpn_spotify_A", "vpn_netflix_A",
                              "torYoutube1", "torYoutube2", "torYoutube3", "torVimeo3", "torVimeo2", "torVimeo1"],
            "File transfer": ["ftps_down_1a", "ftps_down_1b", "ftps_up_2a", "ftps_up_2b", "scp1", "scpDown1",
                              "scpDown2", "scpDown3", "scpDown4", "scpDown5", "scpDown6", "scpUp1", "scpUp2", "scpUp3",
                              "scpUp5", "scpUp6", "sftp1", "sftpDown1", "sftpDown2", "sftpUp1", "sftp_down_3a",
                              "sftp_down_3b", "sftp_up_2a", "sftp_up_2b", "skype_file1", "skype_file2", "skype_file3",
                              "skype_file4", "skype_file5", "skype_file6", "skype_file7", "skype_file8"],
            "VPN-File transfer": ["vpn_skype_files1b", "vpn_skype_files1a", "vpn_sftp_B", "vpn_sftp_A", "vpn_ftps_B",
                                  "vpn_ftps_A"],
            "VoIP": ["facebook_audio1a", "facebook_audio1b", "facebook_audio2a", "facebook_audio2b", "facebook_audio3",
                     "facebook_audio4", "hangouts_audio1a", "hangouts_audio1b", "hangouts_audio2a", "hangouts_audio2b",
                     "hangouts_audio3", "hangouts_audio4", "skype_audio1a", "skype_audio1b", "skype_audio2a",
                     "skype_audio2b", "skype_audio3", "skype_audio4", "voipbuster_4b", "voipbuster_4a", "voipbuster3b",
                     "voipbuster2b", "voipbuster1b"],
            "VPN-VoIP": ["vpn_voipbuster1b", "vpn_voipbuster1a", "vpn_skype_audio2", "vpn_skype_audio1",
                         "vpn_hangouts_audio2", "vpn_hangouts_audio1", "vpn_facebook_audio2"],
            "P2P": ["Torrent01"],
            "VPN-P2P": ["vpn_bittorrent"],
            }

# Datasets and labels.
result_data = [[], []]


# Anonymize the session.
def anonymization(pcaps):
    # Generate source info.
    src_ip = "0.0.0.0"
    src_ipv6 = "0:0:0:0:0:0:0:0"
    src_port = 0
    src_mac = "00:00:00:00:00:00"

    dst_ip = "0.0.0.0"
    dst_ipv6 = "0:0:0:0:0:0:0:0"
    dst_port = 0
    dst_mac = "00:00:00:00:00:00"

    file = b''
    for p in pcaps:

        if 'Ether' in p:
            p.src = src_mac
            p.dst = dst_mac
        if 'IP' in p:
            p["IP"].src = src_ip
            p["IP"].dst = dst_ip
            p["IP"].sport = src_port
            p["IP"].dport = dst_port
        if 'IPv6' in p:
            p["IPv6"].src = src_ipv6
            p["IPv6"].dst = dst_ipv6
            p["IPv6"].sport = src_port
            p["IPv6"].dport = dst_port
        if 'TCP' in p:
            p['TCP'].sport = src_port
            p['TCP'].dport = dst_port
        if 'UDP' in p:
            p['UDP'].sport = src_port
            p['UDP'].dport = dst_port
        if 'ARP' in p:
            p["ARP"].psrc = src_ip
            p["ARP"].pdst = dst_ip
            p["ARP"].hwsrc = src_mac
            p["ARP"].hwdst = dst_mac

        file += bytes_encode(p)

        # trim when the file's length greater than TRIMED_FILE_LEN.
        if len(file) >= TRIMED_FILE_LEN:
            file = file[:TRIMED_FILE_LEN]
            break

    # padding when the file's length less than TRIMED_FILE_LEN.
    if len(file) < TRIMED_FILE_LEN:
        file += b'\x00' * (TRIMED_FILE_LEN - len(file))

    return file


# Extract session features according to quintuple.
def session_extractor(p):
    if 'Raw' not in p:
        return "Other"
    if 'IP' in p:
        ret = list()
        if 'TCP' in p:
            ret.append("TCP")
            ret.append(p["IP.src"] + ":" + str(p['TCP'].sport))
            ret.append(p["IP.dst"] + ":" + str(p['TCP'].dport))
        elif 'UDP' in p:
            ret.append("UDP")
            ret.append(p["IP.src"] + ":" + str(p['UDP'].sport))
            ret.append(p["IP.dst"] + ":" + str(p['UDP'].dport))
        elif 'ICMP' in p:
            ret.append("ICMP")
            ret.append(p["IP.src"])
            ret.append(p["IP.dst"])
            ret.append(str(p["ICMP"].type) + str(p["ICMP"].code) + str(p["ICMP"].id))
        elif 'ICMPv6' in p:
            ret.append("ICMP")
            ret.append(p["IP.src"])
            ret.append(p["IP.dst"])
            ret.append(str(p["ICMPv6"].type) + str(p["ICMPv6"].code) + str(p["ICMPv6"].id))
        ret.sort()
        return "IP " + " ".join(ret)
    elif 'IPv6' in p:
        ret = list()
        if 'TCP' in p:
            ret.append("TCP")
            ret.append(p["IPv6.src"] + ":" + str(p['TCP'].sport))
            ret.append(p["IPv6.dst"] + ":" + str(p['TCP'].dport))
        elif 'UDP' in p:
            ret.append("UDP")
            ret.append(p["IPv6.src"] + ":" + str(p['UDP'].sport))
            ret.append(p["IPv6.dst"] + ":" + str(p['UDP'].dport))
        elif 'ICMP' in p:
            ret.append("ICMP")
            ret.append(p["IPv6.src"])
            ret.append(p["IPv6.dst"])
            ret.append(str(p["ICMP"].type) + str(p["ICMP"].code) + str(p["ICMP"].id))
        elif 'ICMPv6' in p:
            ret.append("ICMP")
            ret.append(p["IPv6.src"])
            ret.append(p["IPv6.dst"])
            ret.append(str(p["ICMPv6"].type) + str(p["ICMPv6"].code) + str(p["ICMPv6"].id))
        ret.sort()
        return "IPv6 " + " ".join(ret)
    elif 'ARP' in p:
        ret = list()
        ret.append(p["ARP"].psrc)
        ret.append(p["ARP"].pdst)
        ret.sort()
        return "ARP " + " ".join(ret)
    return "Other"


# Get the index of the category to which the pcap file belongs.
def get_index(name):
    index = 0
    for cls in CLS_DICT:
        if CLS_DICT[cls].count(name) > 0:
            return index
        index += 1
    return -1


def handle(path):
    # read the pcap files.
    print("read the pcap files:" + path)

    cls = get_index(os.path.splitext(os.path.basename(path))[0])
    if cls < 0:
        print(len(result_data[0]))
        print("read the pcap files complete.")
        return

    # the dict of sessions.
    sessions = defaultdict(PacketList)

    count = 0

    with PcapReader(path) as fdesc:
        # Read 50000 packets at a time.
        pcap_reader = fdesc.read_all(count=ONCE_READ_COUNT)

        while pcap_reader:
            for pcap in pcap_reader:
                key = session_extractor(pcap)
                if key == "Other":
                    continue

                # count of the session has reached SESSION_PACKET_COUNT.
                if len(sessions[key]) > SESSION_PACKET_COUNT:
                    session = sessions[key]
                    # anonymization the session and get a trimed file.
                    file = anonymization(session)

                    bytes = np.frombuffer(file, dtype=np.uint8)

                    # judge whether it is repeated or not
                    bool = False
                    for x in result_data[0]:
                        if (bytes == x).all():
                            bool = True
                    if not bool:
                        result_data[0].append(bytes)
                        result_data[1].append(cls)

                        count += 1
                        if count >= FILE_COUNT:
                            print(len(result_data[0]))
                            print("read the pcap files complete.")
                            return

                    # del the session from sessions to free memory.
                    sessions.pop(key)
                    continue

                # add the pcap to corresponding session.
                sessions[key].append(pcap)
            pcap_reader = fdesc.read_all(count=ONCE_READ_COUNT)

        # handle the remaining sessions.
        for key, session in sessions.items():
            file = anonymization(session)
            bytes = np.frombuffer(file, dtype=np.uint8)
            # judge whether it is repeated or not
            bool = False
            for x in result_data[0]:
                if (bytes == x).all():
                    bool = True
            if not bool:
                result_data[0].append(bytes)
                result_data[1].append(cls)

                count += 1
                if count >= FILE_COUNT:
                    print(len(result_data[0]))
                    print("read the pcap files complete.")
                    return
    print(len(result_data[0]))
    print("read the pcap files complete.")


base_path = r".\tk2016\1_Pcap"
save_path = r".\tk2016\preTraffic.npz"

paths = [os.path.join(base_path, x) for _, x in enumerate(os.listdir(base_path))]
for path in tqdm(paths):
    handle(path)
print("complete all pcap files.")

# shuffle the data.
np.random.seed(1)
np.random.shuffle(result_data[0])
np.random.seed(1)
np.random.shuffle(result_data[1])

# split the data.
train_files_count = math.ceil(len(result_data[0]) * TRAIN_RATIO)
taining_data = result_data[0][:train_files_count]
taining_label = result_data[1][:train_files_count]
test_data = result_data[0][train_files_count:]
test_label = result_data[1][train_files_count:]

np.savez(save_path, taining_data=taining_data, taining_label=taining_label, test_data=test_data,
         test_label=test_label)

print("complete save file.")

