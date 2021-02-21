.open /home/devel/Desktop/AD2.db
.mode csv
.output workdir/graphcache/1/networkx.csv
.separator " "
SELECT src,dst FROM adedges, adedgelookup WHERE adedges.graph_id = 1 AND adedgelookup.id = adedges.src AND adedgelookup.oid IS NOT NULL;
.exit