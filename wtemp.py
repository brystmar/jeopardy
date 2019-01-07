# save the starting timestamp
import datetime, time
now = datetime.datetime.now()
now = now.isoformat(timespec='seconds')

missing_data = [320, 1088, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1150, 1151, 1153, 1165, 1182, 1183, 1218, 1220, 1221, 1385, 1387, 1389, 1434, 1435, 1436, 1437, 1438, 1443, 1444, 1445, 1449, 1665, 1667, 1720, 1721, 1723, 1724, 1725, 1726, 1727, 1728, 1731, 1732, 1733, 1734, 1735, 1736, 1748, 1750, 1752, 3552, 3575, 4246, 4256, 4264, 4271, 4273, 4284, 4757, 4758, 4759, 4760, 4763, 4764, 4765, 4766, 4767, 4960, 4983, 5348, 5361, 5773, 5877]

def write_errors(game_id, msg):
    global errors
    global now

    with open('wtemp_test.txt', 'a') as f:
        # add a header if this is the first time we're writing to this file
        if len(errors) < 1:
            f.write("\n")
            f.write("[script: ja_prr.py on " + str(now).replace('T',' at ') + "]\n")
            f.write(str(game_id) + " " + msg + "\n")
        else:
            f.write(str(game_id) + " " + msg + "\n")


errors = list()

i=0
for m in missing_data:
    if i > 9: quit()
    message = "Stock error msg " + str(i)
    write_errors(m, message)
    errors.append([m, message])
    i += 1

f.write("\n")
f.close()
