from datetime import datetime, timedelta

def parse_time(txt):
    '''08:01:34.422867 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-cli/build/cli/node_modules", 0x7ffcc55afcd0) = -1 ENOENT (No such file or directory)'''
    # NB: There's native support for parsing isoformat in python3.7, but I only
    # have 3.6 installed.
    time_txt = txt.split(' ')[0]
    return datetime.strptime(time_txt, '%H:%M:%S.%f');

def time_difference(t1, t2):
    return (t1 - t2)

if __name__ == '__main__':
    with open('./strace.out') as f:
        lines = f.readlines()

    time_spent_in_stat_usec = timedelta()
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if ' stat(' in line:
            time_spent_in_stat_usec += time_difference(parse_time(line), parse_time(lines[i-1]))

    print(time_spent_in_stat_usec)

