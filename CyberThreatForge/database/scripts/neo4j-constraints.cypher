// Neo4j Constraints & Indexes for CyberThreatForge

CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT ioc_value IF NOT EXISTS FOR (i:IOC) REQUIRE i.value IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT device_hash IF NOT EXISTS FOR (d:Device) REQUIRE d.hash IS UNIQUE;

CREATE INDEX evidence_type IF NOT EXISTS FOR (e:Evidence) ON (e.type);
CREATE INDEX case_status IF NOT EXISTS FOR (c:Case) ON (c.status);
CREATE INDEX ioc_type IF NOT EXISTS FOR (i:IOC) ON (i.type);
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
