SELECT id, name, quota, email FROM users ORDER BY name;

SELECT id, name, owner_id FROM folders ORDER BY name;

SELECT name, size, uploaded_at FROM files WHERE name LIKE ? AND size <= ? AND uploaded_at <= ? ORDER BY size DESC, id LIMIT 20 OFFSET ?;

SELECT user_id, folder_id FROM accesses WHERE level = 'write' ORDER BY folder_id, user_id;

SELECT f.name, d.name AS folder, u.name AS owner FROM files f JOIN folders d ON d.id=f.folder_id JOIN users u ON u.id=d.owner_id ORDER BY f.id;

SELECT u.name AS recipient, d.name AS folder, a.level FROM accesses a JOIN users u ON u.id=a.user_id JOIN folders d ON d.id=a.folder_id ORDER BY d.id, u.id;

SELECT COUNT(*) AS count, COALESCE(SUM(size),0) AS total, MIN(size) AS minimum, MAX(size) AS maximum, AVG(size) AS average FROM files;

SELECT COUNT(*) AS users, COALESCE(SUM(quota),0) AS total_quota, AVG(quota) AS average_quota FROM users;

SELECT d.name, COUNT(f.id) AS count, COALESCE(SUM(f.size),0) AS bytes FROM folders d LEFT JOIN files f ON f.folder_id=d.id GROUP BY d.id HAVING COUNT(f.id) >= ? ORDER BY count DESC, d.id;

SELECT d.name, u.name AS owner, u.quota-COALESCE(s.used,0) AS free FROM folders d JOIN users u ON d.owner_id=u.id LEFT JOIN (SELECT d.owner_id, SUM(f.size) AS used FROM folders d JOIN files f ON f.folder_id=d.id GROUP BY d.owner_id) s ON s.owner_id=u.id WHERE u.quota-COALESCE(s.used,0) >= ? ORDER BY free DESC, d.id;

SELECT uploaded_at, COUNT(*) AS count, SUM(size) AS bytes FROM files GROUP BY uploaded_at ORDER BY uploaded_at DESC;

SELECT DISTINCT name FROM users WHERE email IS NULL ORDER BY name;
