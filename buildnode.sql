.open /home/devel/Desktop/atest.db
.mode csv
.output workdir/graphcache/2/networkx.csv
.separator " "
SELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = 2 AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;
.exit