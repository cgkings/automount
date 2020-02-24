#!/usr/bin/env python2
# -*- coding: utf8 -*-

from __future__ import print_function
import subprocess
from pprint import pprint
from os import system, path, makedirs

# ===== const =====
partitionId = {
    "Native": "83",
    "LVM": "8e"
}
statements = {
    "askForChoice": {
        "en": "Enter your choice: ",
        "zh": "輸入你的選擇: "
    },
    "chooseLanguage": {
        "en": [
            "Choose your favorite language",
            "===============================================",
            "1. English",
            "2. 中文",
            "==============================================="
        ],
        "zh": [
            "選擇您喜歡的語言",
            "===============================================",
            "1. English",
            "2. 中文",
            "==============================================="
        ]
    },
    "error": {
        "unexpectedError": {
            "en": "Unexpected Error.",
            "zh": "意外的錯誤。"
        },
        "notImplemented": {
            "en": "It is not implemented yet.",
            "zh": "尚未實現。"
        },
        "noDataDisk": {
            "en": "No data disks available.",
            "zh": "沒有可用的數據硬碟。"
        },
        "multipleVolumeGroup": {
            "en": "Not valid for multiple volume groups.",
            "zh": "對多個卷組無效。"
        },
        "invalidMountPoint": {
            "en": "{0} is not a valid mount point.",
            "zh": "{0} 不是有效的挂載點。"
        },
        "invalidDisk": {
            "en": "{0} is not a valid disk.",
            "zh": "{0} 不是有效的硬碟。"
        },
        "invalidLV": {
            "en": "{0} is not a valid logical volume.",
            "zh": "{0} 不是有效的邏輯卷。"
        },
        "invalidVG": {
            "en": "{0} is not a valid volume group.",
            "zh": "{0} 不是有效的卷組。"
        },
        "noValidLV": {
            "en": "No valid logical volume was found.",
            "zh": "找不到有效的邏輯卷。"
        },
        "outOfIndex": {
            "en": "Out of index.",
            "zh": "超出索引。"
        },
        "outOfSpace": {
            "en": "Out of space.",
            "zh": "空間不足。"
        },
        "errorMount": {
            "en": "Mount failed.",
            "zh": "挂載失敗。"
        },
        "differentMountPoint": {
            "en": "The partition is mounted on different mount point.",
            "zh": "分區已掛載到不同的掛載點。"
        },
        "fstabFoundError": {
            "en": "Partition with different info is found in fstab file.",
            "zh": "在fstab文件中找到了具有不同信息的分區。"
        },
        "createPartitionFailed": {
            "en": "Failed to create a new partition.",
            "zh": "無法創建新分區。"
        },
    },
    "mainPage": {
        "en": [
            "AutoMount for XenSystem",
            "=================================================",
            "Dangerous operation, only for new VPS",
            "Press q to cancel",
            "1. Use the data disk to extend root partition",
            "2. Mount the data disk as another partition",
            "================================================="
        ],
        "zh": [
            "AutoMount for XenSystem",
            "=================================================",
            "危險操作，僅適用於新的VPS",
            "按 q 取消",
            "1. 使用數據硬碟擴展根分區",
            "2. 將數據硬碟挂載為另一個分區",
            "================================================="
        ]
    },
    "chooseMountPoint": {
        "en": "Enter your preferred mount point (/home, /www): ",
        "zh": "輸入您首選的掛載點 (/home, /www): "
    },
    "chooseDisk": {
        "en": "Enter your preferred disk ({0}): ",
        "zh": "輸入您首選的硬碟 ({0}): "
    },
    "chooseLV": {
        "en": "Enter your preferred logical volume ({0}): ",
        "zh": "輸入您首選的邏輯卷 ({0}): "
    },
    "chooseVG": {
        "en": "Enter your preferred volume group ({0}): ",
        "zh": "輸入您首選的卷組 ({0}): "
    },
    "mountedOK": {
        "en": "The partition is mounted successfully.",
        "zh": "分區已成功掛載。"
    },
    "extendedOK": {
        "en": "The logical volume is extended successfully.",
        "zh": "邏輯卷已成功擴展。"
    }
}

# global variable
defaultLang = "en"
lang = None
mountPoint = None
fstabPath = "/etc/fstab"
fdiskInput = """n
p
{0}


t
{1}
w
"""

def OK(msg):
    print("OK:", msg)

def ERR(msg):
    print("ERR:", msg)

def cls():
    system("clear")

def getOutput(command, input=None):
    #print(command)
    p = subprocess.Popen(command, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, close_fds=True)
    stdout = p.communicate(input=input)[0].decode()
    return stdout

# ===== not used yet begin =====
def getPhysicalVolume(vg):
    output = getOutput("pvs")
    cnt = 0
    for o in output.splitlines():
        if cnt != 0:
            w = o.split()
            if len(w) > 2:
                if w[1] in vg:
                    vg[w[1]]["pv"].append(w[0])
        cnt+=1

def printDisk(disks):
    for k, v in disks.iteritems():
        if v["sectors"] == None:
            continue
        point = []
        for kk, vv in v.iteritems():
            if kk.startswith(k):
                point.append(vv["end"])
        point.sort()
        if len(point) == 0:
            print(' {0:>15}: [{1:<40}]'.format(k, ""))
        else:
            s = ""
            l = 0
            left = 40
            for p in point:
                num = (p - l)*40/v["sectors"]
                if num < 1:
                    num = 1
                elif num > left:
                    if p >= v["sectors"]:
                        num = left
                    else:
                        num = left-2
                s += "#"*num + "|"
                left = 40 - len(s)
                l = p
            if point[-1] >= v["sectors"]:
                s = s[:-1]
            print(' {0:>15}: [{1:<40}]'.format(k, s))
# ===== not used yet end =====

def getMountInfo(partition):
    output = getOutput("mount")
    mountInfo = {
        "type": None,
        "path": None
    }
    for o in output.splitlines():
        w = o.split()
        if len(w) >= 5:
            if (w[0] == partition and w[3] == "type"
                and w[2].startswith("/")):
                mountInfo["path"] = w[2]
                mountInfo["type"] = w[4]
                break
    return mountInfo

def writeFstab(partition, mountPoint, partitionType):
    global fstabPath
    found = False
    with open(fstabPath) as f:
        for line in f:
            if not line.startswith("#"):
                w = line.split()
                if len(w) < 6:
                    continue
                if w[0] == partition:
                    if w[1] == mountPoint and w[2] == partitionType:
                        found = True
                        break
                    else:
                        ERR(statements["error"]["fstabFoundError"][lang])
                        exit(-1)
    if found == False:
        with open(fstabPath, 'a') as f:
            f.write("{0} {1} {2} defaults 1 2\n".format(partition,
                mountPoint, partitionType))

def mountPartition(partition, mountPoint):
    # mkdir
    if not path.exists(mountPoint):
        makedirs(mountPoint)
    else:
        if not path.isdir(mountPoint):
            ERR(statements["error"]["invalidMountPoint"][lang].format(
                mountPoint))
            exit(-1)

    # check if mounted
    mountInfo = getMountInfo(partition)

    # mounted but with different path
    if mountInfo["type"] != None and mountInfo["path"] != mountPoint:
        ERR(statements["error"]["differentMountPoint"][lang])
        exit(-1)

    # it is not mounted
    if mountInfo["type"] == None:
        # try to mount partition
        ret = subprocess.call("mount {0} {1}".format(
            partition, mountPoint).split())
        if ret == 0:
            mountInfo = getMountInfo(partition)
            if (mountInfo["type"] != None and
                    mountInfo["path"] != mountPoint):
                ERR(statements["error"]["differentMountPoint"][lang])
                exit(-1)
        else:
            ERR(statements["error"]["errorMount"][lang])
            exit(-1)

    # the partition is mounted now
    #print("partitionType:", mountInfo["type"])
    writeFstab(partition, mountPoint, mountInfo["type"])

def makeFileSystem(partition, fileSystemType):
    output = getOutput("mkfs -t {0} {1}".format(fileSystemType,
        partition).split())
    print(output)

def createPartition(dname, index, partId):
    output = getOutput("fdisk -u {0}".format(dname).split(),
        input=fdiskInput.format(index, partId))
    print(output)
    disks = getDiskStructure()
    if len(disks[dname]["partition"]) > 0:
        newPartition = dname + str(index)
        if newPartition in disks[dname]["partition"]:
            if disks[dname]["partition"][newPartition]["partId"] == partId:
                return newPartition
    ERR(statements["error"]["createPartitionFailed"][lang])
    exit(-1)

def getDataDisk(disks):
    dname = None
    if "/dev/sdb" in disks:
        dname = "/dev/sdb"
    elif "/dev/xvdb" in disks:
        dname = "/dev/xvdb"
    return dname

def chooseMountPoint():
    mountPoint = None
    while mountPoint == None:
        mountPoint = raw_input(statements["chooseMountPoint"][lang])
        if not mountPoint.startswith("/"):
            ERR(statements["error"]["invalidMountPoint"][lang].format(
                mountPoint))
            mountPoint = None
    return mountPoint

def autoMountEXT(vg, disks):
    global lang
    global mountPoint

    mountPoint = chooseMountPoint()

    if len(disks) > 1:
        # get name of data disk
        dname = getDataDisk(disks)
        if dname == None:
            dname = chooseDisk(disks.keys())

        #print("dname:", dname)
        #print("mountPoint:", mountPoint)

        # data disk exists
        if dname != None:
            if len(disks[dname]["partition"]) == 0:
                # format and mount
                partition = createPartition(dname, 1, partitionId["Native"])
                #print("partition:", partition)
                makeFileSystem(partition, "ext4")
                mountPartition(partition, mountPoint)
                OK(statements["mountedOK"][lang])
            elif len(disks[dname]["partition"]) == 1:
                # try to mount
                partition = disks[dname]["partition"].keys()
                #print("partition:", partition[0])
                mountPartition(partition[0], mountPoint)
                OK(statements["mountedOK"][lang])
            else:
                ERR(statements["error"]["notImplemented"][lang])
                exit(-1)
        else:
            ERR(statements["error"]["noDataDisk"][lang])
            exit(-1)

def chooseDisk(disks):
    selectedDisk = None
    while selectedDisk == None:
        selectedDisk = raw_input(statements["chooseDisk"][lang].format(
            ','.join(disks)))
        if selectedDisk not in disks:
            ERR(statements["error"]["invalidDisk"][lang].format(
                selectedDisk))
            selectedDisk = None
    return selectedDisk

def chooseLV(lv):
    selectedLV = None
    while selectedLV == None:
        selectedLV = raw_input(statements["chooseLV"][lang].format(
            ','.join(lv)))
        if selectedLV not in lv:
            ERR(statements["error"]["invalidLV"][lang].format(selectedLV))
            selectedLV = None
    return selectedLV

def chooseVG(vg):
    selectedVG = None
    while selectedVG == None:
        selectedVG = raw_input(statements["chooseVG"][lang].format(
            ','.join(vg)))
        if selectedVG not in vg:
            ERR(statements["error"]["invalidVG"][lang].format(selectedVG))
            selectedVG = None
    return selectedVG

def extendLV(vg, lv, partition):
    mapperVG = vg.replace("-", "--")
    mapperLV = lv.replace("-", "--")
    mapperPath = "/dev/mapper/{0}-{1}".format(mapperVG, mapperLV)
    mountInfo = getMountInfo(mapperPath)
    if mountInfo["type"] == None:
        ERR(statements["error"]["unexpectedError"][lang])
        exit(-1)

    # create physical volume
    output = getOutput("pvcreate {0}".format(partition).split())
    print(output)

    # extend volume group
    output = getOutput("vgextend {0} {1}".format(vg, partition).split())
    print(output)

    # resize logical volume
    output = getOutput("lvresize -l +100%FREE {0}".format(
        mapperPath).split())
    print(output)

    # resize file system
    if mountInfo["type"] == "xfs":
        output = getOutput("xfs_growfs {0}".format(
            mountInfo["path"]).split())
        print(output)
    else:
        output = getOutput("resize2fs {0}".format(mapperPath).split())
        print(output)

def autoMountLVM(vg, disks):
    global lang

    if len(vg) > 0 and len(disks) > 1:
        # get name of data disk
        dname = getDataDisk(disks)
        if dname == None:
            dname = chooseDisk(disks.keys())

        #print("dname:", dname)
        if len(vg) == 1:
            selectedVG = vg.keys()[0]
        else:
            selectedVG = chooseVG(vg.keys())

        filteredLV = [ x for x in vg[selectedVG]["lv"] if "swap" not in x ]
        if len(filteredLV) == 0:
            ERR(statements["error"]["noValidLV"])
        elif len(filteredLV) == 1:
            selectedLV = filteredLV[0]
        else:
            selectedLV = chooseLV(filteredLV)

        #print("selectedVG:", selectedVG)
        #print("selectedLV:", selectedLV)

        # data disk exists
        if dname != None:
            if disks[dname]["end"] == True:
                ERR(statements["error"]["outOfSpace"][lang])
                exit(-1)

            idx = len(disks[dname]["partition"]) + 1
            if idx <= 4:
                # format and mount
                partition = createPartition(dname, idx, partitionId["LVM"])
                extendLV(selectedVG, selectedLV, partition)
                OK(statements["extendedOK"][lang])
                pass
            else:
                ERR(statements["error"]["outOfIndex"][lang])
                exit(-1)
        else:
            ERR(statements["error"]["noDataDisk"][lang])
            exit(-1)

def autoMount(vg, disks):
    cls()
    print()
    for i in statements["mainPage"][lang]:
        print(i)
    print()

    choice = None
    while choice == None:
        choice = raw_input(statements["askForChoice"][lang])
        if choice == "1":
            autoMountLVM(vg, disks)
        elif choice == "2":
            autoMountEXT(vg, disks)
        elif choice == "q":
            exit()
        else:
            choice = None

def getDiskStructure():
    disks = {}
    output = getOutput("fdisk -l -u".split())
    curr = None
    idx = {
        "Boot": None,
        "Start": None,
        "End": None,
        "Id": None
    }
    for o in output.splitlines():
        if o.startswith("Disk "):
            w = o.split()
            if len(w) > 2 and w[1].startswith("/"):
                if "mapper" in w[1]:
                    curr = None
                    continue
                curr = w[1].rstrip(":")
                disks[curr] = {
                    "partition": {},
                    "end": False,
                    "sectors": None
                }
                if w[-1] == "sectors":
                    disks[curr]["sectors"] = int(w[-2])
        elif (curr != None and disks[curr]["sectors"] == None
                and o.endswith("sectors")):
            i = o.rindex("sectors")
            o = o[:i]
            w = o.split()
            disks[curr]["sectors"] = int(w[-1])
        elif curr != None and o.strip().startswith("Device"):
            if ("Device" in o and "Boot" in o and "Start" in o
                    and "End" in o and "Id" in o):
                w = o.split()
                idx["Boot"] = w.index("Boot")
                idx["Start"] = w.index("Start")
                idx["End"] = w.index("End")
                idx["Id"] = w.index("Id")
        elif curr != None and o.startswith(curr):
            w = o.split()
            if len(w) >= 6:
                p = w[0]
                if w[idx["Boot"]] == "*":
                    w.pop(idx["Boot"])
                disks[curr]["partition"][p] = {
                    "partId": w[idx["Id"]-1],
                    "begin": int(w[idx["Start"]-1]),
                    "end": int(w[idx["End"]-1])
                }

                if (disks[curr]["partition"][p]["end"] + 1 >=
                        disks[curr]["sectors"]):
                    disks[curr]["end"] = True
    return disks

def obtainLogicalVolume(vg):
    output = getOutput("lvs")
    cnt = 0
    for o in output.splitlines():
        if cnt != 0:
            w = o.split()
            if len(w) > 2:
                if w[1] in vg:
                    vg[w[1]]["lv"].append(w[0])
        cnt+=1

def getVolGroup():
    output = getOutput("vgs")
    vg = {}
    cnt = 0
    for o in output.splitlines():
        if cnt != 0:
            w = o.split()
            if len(w) > 1:
                vg[w[0]] = {
                    "pv": [],
                    "lv": []
                }
        cnt+=1
    return vg

def chooseLanguage():
    global lang
    global defaultLang

    cls()
    print()
    for i in statements["chooseLanguage"][defaultLang]:
        print(i)
    print()

    while lang == None:
        lang = raw_input("Enter your choice: ")
        if lang == "1":
            lang = "en"
        elif lang == "2":
            lang = "zh"
        else:
            lang = None
    return lang

if __name__ == "__main__":
    # choose language
    chooseLanguage()

    try:
        # precheck
        vg = getVolGroup()
        obtainLogicalVolume(vg)
        disks = getDiskStructure()
        if len(disks) < 2:
            ERR(statements["error"]["noDataDisk"][lang])
            exit(-1)
        #if len(vg) > 1:
        #    ERR(statements["error"]["multipleVolumeGroup"][lang])
        #    exit(-1)
        #pprint(disks)
        #raw_input("test")

        # start autoMount
        autoMount(vg, disks)
    except Exception as e:
        print(e)
        ERR(statements["error"]["unexpectedError"][lang])
        exit(-1)
