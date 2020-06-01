from math import atan, sinh, pi, degrees
import re

def tile_ul(x, y, z):
    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * y / n)))
    lat_deg = degrees(lat_rad)
    return  lon_deg,lat_deg

def pathToTile(path):
    m = re.search(r'^\/(\d+)\/(\d+)\/(\d+)\.(\w+)', path)
    if (m):
        return {'zoom':   int(m.group(1)),
                'x':      int(m.group(2)),
                'y':      int(m.group(3)),
                'format': m.group(4)}
    else:
        return None

def tileIsValid(tile):
    if not ('x' in tile and 'y' in tile and 'zoom' in tile):
        return False
    if 'format' not in tile or tile['format'] not in ['pbf', 'mvt', 'png']:
        return False
    size = 2 ** tile['zoom']
    if tile['x'] >= size or tile['y'] >= size:
        return False
    if tile['x'] < 0 or tile['y'] < 0:
        return False
    return True

def tileToEnvelope(tile):
        # Width of world in EPSG:3857
        worldMercMax = 20037508.3427892
        worldMercMin = -1 * worldMercMax
        worldMercSize = worldMercMax - worldMercMin
        # Width in tiles
        worldTileSize = 2 ** tile['zoom']
        # Tile width in EPSG:3857
        tileMercSize = worldMercSize / worldTileSize
        # Calculate geographic bounds from tile coordinates
        # XYZ tile coordinates are in "image space" so origin is
        # top-left, not bottom right
        env = dict()
        env['xmin'] = worldMercMin + tileMercSize * tile['x']
        env['xmax'] = worldMercMin + tileMercSize * (tile['x'] + 1)
        env['ymin'] = worldMercMax - tileMercSize * (tile['y'] + 1)
        env['ymax'] = worldMercMax - tileMercSize * (tile['y'])
        return env

# Generate SQL to materialize a query envelope in EPSG:3857.
# Densify the edges a little so the envelope can be
# safely converted to other coordinate systems.
def envelopeToBoundsSQL(env):
    DENSIFY_FACTOR = 4
    env['segSize'] = (env['xmax'] - env['xmin'])/DENSIFY_FACTOR
    sql_tmpl = 'ST_Segmentize(ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, 3857),{segSize})'
    return sql_tmpl.format(**env)

# Generate a SQL query to pull a tile worth of MVT data
# from the table of interest.
def envelopeToSQL(env, table):
    tbl = table.copy()
    tbl['env'] = envelopeToBoundsSQL(env)
    # Materialize the bounds
    # Select the relevant geometry and clip to MVT bounds
    # Convert to MVT format
    sql_tmpl = """
        WITH
        bounds AS (
            SELECT {env} AS geom,
                    {env}::box2d AS b2d
        ),
        mvtgeom AS (
            SELECT ST_AsMVTGeom(ST_Transform(t.{geomColumn}, 3857), bounds.b2d) AS geom,
                    {attrColumns}
            FROM {table} t, bounds
            WHERE ST_Intersects(t.{geomColumn}, ST_Transform(bounds.geom, {srid}))
        )
        SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom
    """
    return sql_tmpl.format(**tbl)


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