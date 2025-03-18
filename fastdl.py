import os, asyncio, quart, hypercorn
from quart import abort, send_from_directory

app = quart.Quart(__name__)

path = "/home/eli/_games/"
allowed_folders = ( # allowed subfolders (e.g. /tf/maps/)
    "maps/",
    "gfx/",
    "models/",
    "materials/",
    "sound/",
    "sprites/",
    "logos/",
    "particles/",
    "resource/"
)
allowed_filetypes = (
    ".wad",
    "mapcycle.txt",
)

paths = {
    "tf":         path+"tf2/tf/",
    "garrysmod":  path+"gmod/garrysmod/",
    "hl2mp":      path+"hl2mp/hl2mp",
    "valve":      path+"hldm/valve/",
    "svencoop":   path+"sven/svencoop/",
    "doom":       path+"doom/wads/" # zandronum only
}

@app.route('/')
async def index():
    return quart.redirect("https://elisttm.space")

@app.route('/<game>/<path:file>')
async def fastdl(game, file):
    game = game.lower()
    if game in paths and os.path.exists(paths[game]+file) and (file.lower().startswith(allowed_folders) or file.lower().endswith(allowed_filetypes)):
        print(f"[{game}] serving {file}")
        return await send_from_directory(paths[game], file)
    print(f"[{game}] [404] {file} requested but not found")
    return await abort(404)

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:27111"]
app.jinja_env.cache = {}

if __name__ == '__main__':
	asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
