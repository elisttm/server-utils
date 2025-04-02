import os, asyncio, quart, hypercorn
from quart import abort, send_from_directory

app = quart.Quart(__name__)

path = "/home/eli/_games/"
allowed_folders = ( # allowed subfolders (e.g. /tf/maps/)
    "maps/",
    "gfx/",
    "models/",
    "materials/",
    "scripts/",
    "sound/",
    "sprites/",
    "logos/",
    "particles/",
    "resource/",
    "download/",
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
    "doom":       path+"doom/wads/", # zandronum only
    "halo":       path+"eldewrito/download/" # eldewrito
}

async def construct_filelist(game, path):
    fullpath = paths[game]+path
    html = ""
    for folder in [d for d in sorted(os.listdir(fullpath), key=str.casefold) if os.path.isdir(fullpath+d)]:
        html += f'<b><a href="/{os.path.join(game, path, folder)}/">/{folder}/</a></b><br>'
    for file in [d for d in sorted(os.listdir(fullpath), key=str.casefold) if os.path.isfile(fullpath+d)]:
        html += f'- <a href="/{os.path.join(game, path, file)}">{file}</a><br>'
    return f"<h1>index of /{game}/{path}</h1><hr><ul>{html}</ul>"

@app.route('/')
async def index():
    return quart.redirect("https://elisttm.space")

@app.route('/<game>/<path:path>')
async def fastdl(game, path):
    game = game.lower()
    if game in paths and os.path.exists(paths[game]+path) and (path.lower().startswith(allowed_folders) or path.lower().endswith(allowed_filetypes)):
        if path.lower().endswith(".bz2"):
            return await abort(404)
        if os.path.isdir(paths[game]+path):
            return await construct_filelist(game, path)
        print(f"[{game}] serving {path}")
        return await send_from_directory(paths[game], path)
    print(f"[{game}] [404] {path} requested but not found")
    return await abort(404)

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:27111"]
app.jinja_env.cache = {}

if __name__ == '__main__':
	asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
