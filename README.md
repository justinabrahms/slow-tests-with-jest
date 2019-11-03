# Why does just importing sequelize take 300ms?


```
$ npm test

> slow-js-tests@1.0.0 test /home/abrahms/src/github.com/justinabrahms/slow-js-tests
> jest

 PASS  test/foo.test.js
  ✓ should import sequelize quickly (316ms)

  console.time test/foo.test.js:7
    everything: 11ms

  console.time test/foo.test.js:5
    sequelize-import-time: 313ms

Test Suites: 1 passed, 1 total
Tests:       1 passed, 1 total
Snapshots:   0 total
Time:        0.972s, estimated 2s
Ran all test suites.
```


When running it with strace enabled, it's quite a bit slower, but we
get information on the timing of the underlying system calls. We can
see that we `stat` many non-existant files as we try to resolve where
to find the file to import. You can run strace like:

```
strace -tt -o ./strace.out ./node_modules/.bin/jest test/foo.test.js
```

If you're using OSX, you'll need to use dtrace instead. The `dtrace`
command below monitors a binary (in this case `node`). Once you run
this, you can launch the tests as in the first example and the results
will be written to `require.log`.

```
sudo dtruss -d -n 'node' > /tmp/require.log 2>&1
```


From there, we can see node trying to resolve the modules by looking
for various non-existant files before finding a relevant
`package.json` and ultimately finding the file. All of this took
1.5ms for just a single import.

```
08:01:34.422867 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-cli/build/cli/node_modules", 0x7ffcc55afcd0) = -1 ENOENT (No such file or directory)
08:01:34.423075 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-cli/build/node_modules", 0x7ffcc55afcd0) = -1 ENOENT (No such file or directory)
08:01:34.423210 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-cli/node_modules", 0x7ffcc55afcd0) = -1 ENOENT (No such file or directory)
08:01:34.423374 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules", {st_mode=S_IFDIR|0755, st_size=4096, ...}) = 0
08:01:34.423496 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-config", 0x7ffcc55afcd0) = -1 ENOENT (No such file or directory)
08:01:34.423592 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-config.js", 0x7ffcc55afc00) = -1 ENOENT (No such file or directory)
08:01:34.423697 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-config.json", 0x7ffcc55afc00) = -1 ENOENT (No such file or directory)
08:01:34.423783 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest/node_modules/jest-config.node", 0x7ffcc55afc00) = -1 ENOENT (No such file or directory)
08:01:34.423864 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules", {st_mode=S_IFDIR|0755, st_size=16384, ...}) = 0
08:01:34.423980 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest-config", {st_mode=S_IFDIR|0755, st_size=4096, ...}) = 0
08:01:34.424070 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest-config.js", 0x7ffcc55afc00) = -1 ENOENT (No such file or directory)
08:01:34.424170 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest-config.json", 0x7ffcc55afc00) = -1 ENOENT (No such file or directory)
08:01:34.424316 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest-config.node", 0x7ffcc55afc00) = -1 ENOENT (No such file or directory)
08:01:34.424444 openat(AT_FDCWD, "/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest-config/package.json", O_RDONLY|O_CLOEXEC) = 21
08:01:34.424548 pread64(21, "{\n  \"_from\": \"jest-config@^24.9."..., 32768, 0) = 2165
08:01:34.424598 close(21)               = 0
08:01:34.424808 stat("/home/abrahms/src/github.com/justinabrahms/slow-js-tests/node_modules/jest-config/build/index.js", {st_mode=S_IFREG|0644, st_size=13446, ...}) = 0
```

We can sum up the amount of time we spend just `stat`ing files with a
small python script. This script will loop over all the lines in our
strace file, calculate how long it took by comparing the timestamp to
the previous line's timestamp, and sum the results.

```python
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
```

The full run on my system looks like this:

```
$ strace -tt -o ./strace.out ./node_modules/.bin/jest test/foo.test.js
 PASS  test/foo.test.js
  ✓ should import sequelize quickly (993ms)

  console.time test/foo.test.js:7
    everything: 16ms

  console.time test/foo.test.js:5
    sequelize-import-time: 988ms

Test Suites: 1 passed, 1 total
Tests:       1 passed, 1 total
Snapshots:   0 total
Time:        2.736s, estimated 6s
Ran all test suites matching /test\/foo.test.js/i.

$ python3 time-check.py
0:00:01.463290
```

This means we spend nearly 1.5 seconds just looking around for files,
most of which don't exist.


## Further reading
- https://kevin.burke.dev/kevin/node-require-is-dog-slow/ (2015)
