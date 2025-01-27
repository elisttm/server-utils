import os, asyncio, quart, hypercorn
from quart import abort, send_from_directory

app = quart.Quart(__name__)

path = "/home/eli/_games/"
allowed_folders = ("maps", "gfx", "models", "materials", "sound", "sprites", "logos", "particles", "resource") # allowed subfolders (e.g. /garrysmod/maps/)

paths = {
    "valve":      path+"hldm/valve/",
    "tf":         path+"tf2/tf/",
    "garrysmod":  path+"gmod/garrysmod/",
    "svencoop":   path+"sven/svencoop/"
}

@app.route('/<game>/<path:filename>')
async def fastdl(game, filename):
    if game in paths and os.path.exists(paths[game]+filename) and (filename.startswith(allowed_folders) or filename.endswith(".wad")):
        print(f"[{game}] serving {filename}...")
        return await send_from_directory(paths[game], filename)
    print(f"[{game}] [404] {filename} requested but not found...")
    return await abort(404)

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:27111"]
app.jinja_env.cache = {}

if __name__ == '__main__':
	asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
