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
