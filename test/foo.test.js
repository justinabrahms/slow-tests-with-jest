console.time('everything');
it('should import sequelize quickly', () => {
  console.time('sequelize-import-time');
  require('sequelize');
  console.timeEnd('sequelize-import-time');
});
console.timeEnd('everything');
