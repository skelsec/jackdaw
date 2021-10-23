.open /home/devel/Desktop/test.db
.mode csv
.output /home/devel/Desktop/aaaaa2aaa/graphcache/1/networkx.csv
.separator " "
SELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = 1 AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;
.exit