.open /home/devel/Desktop/atest.db
.mode csv
.output workdir/graphcache/3/networkx.csv
.separator " "
SELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = 3 AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;
.exit