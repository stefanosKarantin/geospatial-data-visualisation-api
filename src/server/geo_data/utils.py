from math import atan, sinh, pi, degrees

def tile_ul(x, y, z):
    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * y / n)))
    lat_deg = degrees(lat_rad)
    return  lon_deg,lat_deg

# def get_tile(z,x,y):
#     xmin,ymin = tile_ul(x, y, z)
#     xmax,ymax = tile_ul(x + 1, y + 1, z)

#     tile = None

#     tilefolder = "{}/{}/{}".format(CACHE_DIR,z,x)
#     tilepath = "{}/{}.pbf".format(tilefolder,y)
#     if not os.path.exists(tilepath):
#         conn = psycopg2.connect('dbname=geo24 user=geo password=geo host=localhost')
#         cur = conn.cursor()

#         query = "SELECT ST_AsMVT(tile) FROM (SELECT id, name, ST_AsMVTGeom(geom, ST_Makebox2d(ST_transform(ST_SetSrid(ST_MakePoint(%s,%s),4326),3857),ST_transform(ST_SetSrid(ST_MakePoint(%s,%s),4326),3857)), 4096, 0, false) AS geom FROM admin_areas) AS tile"
#         cur.execute(query,(xmin,ymin,xmax,ymax))
#         tile = str(cur.fetchone()[0])

#         if not os.path.exists(tilefolder):
#             os.makedirs(tilefolder)

#         with open(tilepath, 'wb') as f:
#             f.write(tile)
#             f.close()

#         cur.close()
#         conn.close()
#     else:
#         tile = open(tilepath, 'rb').read()

#     return tile