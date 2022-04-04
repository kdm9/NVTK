#!/usr/bin/env python


import sys
import usb.core                 # based on https://walac.github.io/pyusb/
import usb.util
import pandas as pd
import argparse
import getpass
import time
import pdb
# To send commands, we need an Endpoint.

# To get to the endpoint we need to descend down the hierarchy of
# 1. Device
VENDOR = 0x1203
PRODUCT = 0x0243
# 2. Configuration 
CONFIGURATION = 1       # 1-based
# 3. Interface
INTERFACE = 0           # 0-based
# 4. Alternate setting
SETTING = 0             # 0-based
# 5. Endpoint
ENDPOINT = 0            # 0-based



def usb_write(command, device):

    # 1. Device
    # device = usb.core.find(idVendor=VENDOR, idProduct=PRODUCT)
    device.reset()
    if device is None:
        print("The printer is not connected or not turned on!")
        sys.exit(1)

    # By default, the kernel will claim the device and make it available via
    # /dev/usb/hiddevN and /dev/hidrawN which also prevents us
    # from communicating otherwise. This removes these kernel devices.
    # Yes, it is weird to specify an interface before we get to a configuration.
    if device.is_kernel_driver_active(INTERFACE):
        print("Detaching kernel driver")
        device.detach_kernel_driver(INTERFACE)

    # 2. Configuration
    # A Device may have multiple Configurations, and only one can be active at
    # a time. Most devices have only one. Supporting multiple Configurations
    # is reportedly useful for offering more/less features when more/less
    # power is available.
    ## Because multiple configs are rare, the library allows to omit this:
    ## device.set_configuration(CONFIGURATION)
    configuration = device.get_active_configuration()

    # 3. Interface
    # A physical Device may have multiple Interfaces active at a time.
    # A typical example is a scanner-printer combo.
    #
    # 4. Alternate setting
    # I don't quite understand this, but they say that if you need Isochronous
    # Endpoints (read: audio or video), you must go to a non-primary
    # Alternate Setting.
    interface = configuration[(INTERFACE, SETTING)]

    # 5. Endpoint
    # The Endpoint 0 is reserved for control functions
    # so we use Endpoint 1 here.
    # If an Interface uses multiple Endpoints, they will differ
    # in transfer modes:
    # - Interrupt transfers (keyboard): data arrives soon, with error detection
    # - Isochronous transfers (camera): data arrives on time, or gets lost
    # - Bulk transfers (printer): all data arrives, sooner or later
    endpoint = interface[ENDPOINT]

    # Finally!
    endpoint.write(command)

# SIZE 100 mm,17 mm
# GAP 0 mm,1 mm
# DIRECTION 1
# CLS\BACKFEED 204
# QRCODE 0,0,H,3,A,0,"TEST"
# TEXT 100,0,"3",0,1,1,"TEST"
# PRINT 1,1


def create_print_command(ld, user=getpass.getuser(), layout=1, max_field_text_length=18):
    """
    Creates the printer commands, given a dictionary with the entries
    :param ld: dictionary with the label data
    :return: string with the print command
    """

    # Preprocess data
    #pdb.set_trace()
    for k in ld.keys():
        ld[k] = str(ld[k]).upper()
        ld[k] = ld[k][0:min(len(ld[k]), max_field_text_length)]
    user = user[0:min(len(user), 5)]
    user = user.upper()

    # Build command string
    if layout == 1:
        qrcode_string = ld['ID'] + ',' + ld['Group'] + ',' + ld['Replicate']
        #print_cmd = 'SIZE 100 mm,17 mm\nGAP 1 mm,1 mm\nDIRECTION 1\nCLS\n' + \
        print_cmd = 'SIZE 100 mm,17 mm\nGAP 1 mm,1 mm\nDIRECTION 1\nCLS\n' + \
                    'QRCODE 60,5,H,3,A,0,M1,"' + \
                    qrcode_string + \
                    '"\nQRCODE 300,5,H,3,A,90,"' + \
                    qrcode_string + \
                    '"\nTEXT 140,10,"3",0,1,1,"' + \
                    ld['ID'] + \
                    '"\nTEXT 140,48,"3",0,1,1,"' + \
                    user + \
                    '"\nTEXT 320,10,"3",0,1,1,"G:' + \
                    ld['Group'] + \
                    '"\nTEXT 320,48,"3",0,1,1,"R:' + \
                    ld['Replicate'] + \
                    '"\nTEXT 420,10,"3",0,1,1,"' + \
                    ld['Experiment_Id'] + \
                    '"\nTEXT 420,48,"3",0,1,1,"' + \
                    ld['Date'] + \
                    '"\nPRINT 1,1\n'
    elif layout == 2:
        print_cmd = 'SIZE 100 mm,17 mm\nGAP 1 mm,1 mm\nDIRECTION 1\nCLS\n' + \
                        'TEXT 60,10,"3",0,2,2,"' + \
                        ld['ID'] + \
                        '"\nPRINT 1,1\n'
    elif layout == 3:
        print_cmd = 'SIZE 100 mm,17 mm\nGAP 1 mm,1 mm\nDIRECTION 1\nCLS\n' + \
                    'TEXT 40,10,"4",0,1,1,"' + \
                    ld['ID'] + \
                    '"\nTEXT 40,50,"4",0,1,1,"R:' + \
                    ld['Replicate'] + \
                    '"\nTEXT 470,10,"4",0,1,1,"G:' + \
                    ld['Group'] + \
                    '"\nTEXT 150,50,"4",0,1,1,"' + \
                    ld['Date'] + \
                    '"\nTEXT 540,50,"2",0,1,1,"' + \
                    user + \
                    '"\nPRINT 1,1\n'
    elif layout == 4:
        print_cmd = 'SIZE 100 mm,17 mm\nGAP 1 mm,1 mm\nDIRECTION 1\nCLS\n' + \
                    'TEXT 40,10,"4",0,1,1,"' + \
                    ld['ID'] + \
                    '"\nTEXT 40,50,"4",0,1,1,"R:' + \
                    ld['Replicate'] + \
                    '"\nPRINT 1,1\n'
    elif layout == 5:
        print_cmd = 'SIZE 100 mm,17 mm\nGAP 1 mm,1 mm\nDIRECTION 1\nCLS\n' + \
                    'QRCODE 50,3,H,4,A,0,M1,"' + ld["id"] + '"\n' + \
                    'TEXT 160,10,"3",0,1,1,"' + ld['id'] + '"\n' + \
                    'TEXT 160,48,"3",0,1,1,"A:' + ld['accession'] + '"\n' + \
                    'TEXT 320,48,"3",0,1,1,"P:' + ld['within_tray_pos'] + '"\n' + \
                    'TEXT 300,10,"3",0,1,1,"H:' + ld['isolate'] + '"\n' + \
                    'TEXT 460,48,"3",0,1,1,"T:' + ld['timepoint'] + '"\n' + \
                    'TEXT 550,48,"3",0,1,1,"R:' + ld['rep'] + '"\n' + \
                    'TEXT 480,10,"3",0,1,1,"' + ld['date'] + '"\n' + \
                    'PRINT 1,1\n'
    return print_cmd


if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--csv", required=True,
                    help="CSV file with labels. It should have a header and the following fields:\n"
                         "ID,Group,Replicate,Date,Experiment_Id\n"
                         "The fields ID, Group and Replicate are encoded in the QR code. Case-sensitive!")

    ap.add_argument("-r", "--range", required=False,
                    help="Optional, two comma-separated values to print only a range r with a <= r < b, starting with 0.",
                    default=None)

    ap.add_argument("-l", "--layout", required=False,
                    help="Optional, layout options are 1: ID,Group,Replicate,Date,Experiment_Id + user with ID,Group,Replicate in QR code\n"
                         "2: No QR code. ID in big font."
                         "3: No QR code. 1st line: ID and group. 2nd line: Replicate, Date and user."
                         "All fields in a big font except user."
                         "4: No QR code, 1st line: ID, 2nd line replicate.",
                    type=int, default=1)

    ap.add_argument("-u", "--user", required=False,
                    help="Override user name to print on the labels. Default is logged in user",
                    default=getpass.getuser())
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="Actually *do* nothing, just print the printer protocol commands to stdout.")
    args = vars(ap.parse_args())

    # Read CSV and create labels from it
    labels = pd.read_csv(args['csv'])

    if args['range'] is not None:
        print_range=args['range'].split(',')
        print_range = [int(i) for i in print_range]
    else:
        print_range = None

    # CSV: ID:NNNN, Replicate:NNN, Date: YYYY-MM-DD, Experiment_Id: AANNNN
    
    device = None
    if not args["dry_run"]:
        device = usb.core.find(idVendor=VENDOR, idProduct=PRODUCT)
        if device is None:
            raise Exception('Printer device not found! Check connection!')

    for l in range(len(labels)):
        if print_range is None or (l >= print_range[0] and l < print_range[1]):
            if l % 10 == 0:
                time.sleep(1)
            else:
                time.sleep(0.2)
            print_cmd = create_print_command(labels.iloc[[l]].to_dict(orient='records')[0], user=args['user'],layout=args['layout'], max_field_text_length=22)
            if args["dry_run"]:
                print(print_cmd)
            else:
                usb_write(print_cmd.encode('ascii'), device)
                device.reset()
