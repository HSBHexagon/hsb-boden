PRAGMA foreign_keys=ON;
CREATE TABLE meta(id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL DEFAULT 0,write_id TEXT NOT NULL DEFAULT '');
INSERT INTO meta(id) VALUES(1);
CREATE TABLE workers(id TEXT PRIMARY KEY,data TEXT NOT NULL CHECK(json_valid(data)));
CREATE TABLE projects(id TEXT PRIMARY KEY,number TEXT NOT NULL COLLATE NOCASE UNIQUE,data TEXT NOT NULL CHECK(json_valid(data)));
CREATE TABLE assignments(id TEXT PRIMARY KEY,worker_id TEXT NOT NULL REFERENCES workers(id),project_id TEXT NOT NULL REFERENCES projects(id),day TEXT NOT NULL,data TEXT NOT NULL CHECK(json_valid(data)),UNIQUE(worker_id,day));
CREATE INDEX assignments_project_day ON assignments(project_id,day);
CREATE TABLE absences(id TEXT PRIMARY KEY,worker_id TEXT NOT NULL REFERENCES workers(id),from_day TEXT NOT NULL,to_day TEXT NOT NULL,data TEXT NOT NULL CHECK(json_valid(data)),CHECK(to_day>=from_day));
CREATE INDEX absences_worker_days ON absences(worker_id,from_day,to_day);
CREATE TABLE users(email TEXT PRIMARY KEY COLLATE NOCASE,role TEXT NOT NULL CHECK(role IN('admin','planner','viewer','disabled')));
INSERT INTO users(email,role) VALUES('j-cherino@hsb-boden.de','admin'),('j-post@hsb-boden.de','admin');
CREATE TABLE audit(id TEXT PRIMARY KEY,revision INTEGER UNIQUE NOT NULL,at TEXT NOT NULL,actor TEXT NOT NULL,kind TEXT NOT NULL,message TEXT NOT NULL,digest TEXT NOT NULL,detail TEXT NOT NULL);
CREATE TABLE backups(id TEXT PRIMARY KEY,revision INTEGER NOT NULL UNIQUE,at TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)));
CREATE VIEW snapshot AS SELECT json_object('version',3,
'workers',json((SELECT coalesce(json_group_array(json(data)),'[]') FROM workers)),
'projects',json((SELECT coalesce(json_group_array(json(data)),'[]') FROM projects)),
'assignments',json((SELECT coalesce(json_group_array(json(data)),'[]') FROM assignments)),
'absences',json((SELECT coalesce(json_group_array(json(data)),'[]') FROM absences)),
'history',json((SELECT coalesce(json_group_array(json_object('id',id,'at',at,'message',message)),'[]') FROM (SELECT id,at,message FROM audit ORDER BY revision DESC LIMIT 250)))) AS payload;
CREATE TABLE user_audit(id TEXT PRIMARY KEY,at TEXT NOT NULL,actor TEXT NOT NULL,email TEXT NOT NULL,role TEXT NOT NULL);
