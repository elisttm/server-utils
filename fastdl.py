import os, re, datetime, asyncio, quart, hypercorn
from quart import abort, send_from_directory

app = quart.Quart(__name__)

scraper_filter = re.compile("wp-|\\.(env|git|php?|\\.)")

path = "/home/eli/_games/"
allowed_folders = ( # allowed subfolders (e.g. /tf/maps/)
    "maps",
    "gfx",
    "models",
    "materials",
    "scripts",
    "sound",
    "sprites",
    "logos",
    "particles",
    "resource",
    "download",
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

def byte_size(num):
    step = 1024.0
    if num == 0:
        return "--"
    for x in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < step:
            return "%3.1f %s" % (num, x)
        num /= step

async def construct_filelist(game, path):
    fullpath = paths[game]+path
    html = ""
    for folder in [d for d in sorted(os.listdir(fullpath), key=str.casefold) if os.path.isdir(fullpath+d)]:
        html += f'<tr><td><a href="/{os.path.join(game, path, folder)}/">/{folder}/</a></td><td align="right">-</td><td align="right">-</td></tr>'
    for file in [d for d in sorted(os.listdir(fullpath), key=str.casefold) if os.path.isfile(fullpath+d)]:
        stat = os.stat(os.path.join(fullpath, file))
        html += f'<tr><td><a href="/{os.path.join(game, path, file)}">{file}</a></td><td align="right">{byte_size(stat.st_size)}</td><td align="right">&nbsp; {datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S") if stat.st_mtime else "-"}</td></tr>'
    return f"""
<!DOCTYPE html>
<html><body>
    <h1>index of /{game}/{path}</h1>
    <table>
        <tr><th colspan="3"><hr></th></tr>
        {'<tr><td><a href="..">..</a></td><td>&nbsp;</td><td>&nbsp;</td></tr>' if path[:-1] not in allowed_folders else ""}
        {html}
    </table>
    <p>meow! | <a href="https://eli.toys/">eli.toys</a> | <a href="https://github.com/elisttm/server-utils/blob/main/fastdl.py">source code</a></p>
</body></html>
"""

@app.route('/')
async def index():
    return quart.redirect("https://eli.toys/")

@app.route('/<game>/<path:path>')
async def fastdl(game, path):
    if scraper_filter.match(game+path):
        await tarpit
    game = game.lower()
    if game in paths and os.path.exists(paths[game]+path) and (path.lower().startswith(allowed_folders) or path.lower().endswith(allowed_filetypes)):
        if path.lower().endswith(".bz2"):
            return await abort(404)
        if os.path.isdir(paths[game]+path):
            return await construct_filelist(game, os.path.join(path, ''))
        print(f"[{game}] serving {path}")
        return await send_from_directory(paths[game], path)
    print(f"[{game}] [404] {path} requested but not found")
    return await abort(404)

async def tarpit():
    if not scraper_filter.match(path):
        return quart.abort(404)
    async def infinite_load():
        try:
            while True:
                yield b" "
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            return
        except Exception:
            return
    response = await quart.make_response(infinite_load())
    response.timeout = None
    response.headers['Content-Type'] = 'text/plain'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:27111"]
app.jinja_env.cache = {}

if __name__ == '__main__':
	asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
