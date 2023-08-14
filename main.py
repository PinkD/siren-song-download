import asyncio
import json
import os.path

import aiohttp
import aiofiles

song_list_url = "https://monster-siren.hypergryph.com/api/songs"


def song_url(song_id) -> str:
    return f"https://monster-siren.hypergryph.com/api/song/{song_id}"


def album_url(album_id) -> str:
    return f"https://monster-siren.hypergryph.com/api/album/{album_id}/detail"


def ext(path: str) -> str:
    return path.split(".")[-1]


async def urlopen(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


async def get_json(url: str) -> dict:
    data = await urlopen(url)
    data = json.loads(data.decode())
    if data["code"] != 0:
        print(data["msg"])
        exit(1)
    return data["data"]


async def write_file(filename: str, data):
    parent = os.path.dirname(filename)
    if not os.path.exists(parent):
        os.mkdir(parent, 0o755)
    async with aiofiles.open(filename, "wb") as f:
        await f.write(data)


async def download_file(url: str, filename: str):
    if os.path.exists(filename):
        print(f"{filename} exist, skip download")
        return
    print(f"downloading {filename}")
    data = await urlopen(url)
    await write_file(filename, data)


async def download_song(album: str, name: str, url: str):
    filename = f"{album}/{album} - {name}.wav"
    if len(album) == 0:
        filename = f"{name}.wav"
    await download_file(url, filename)


async def download_lrc(album: str, name: str, url: str):
    if not url:
        return
    filename = f"{album}/{album} - {name}.lrc"
    if len(album) == 0:
        filename = f"{name}.lrc"
    await download_file(url, filename)


async def download_cover(album_name: str, cover_url: str, cover_de_url: str):
    filename = f"{album_name}/cover.{ext(cover_url)}"
    await download_file(cover_url, filename)

    filename = f"{album_name}/cover.de.{ext(cover_de_url)}"
    await download_file(cover_de_url, filename)


async def main():
    songs = await get_json(song_list_url)
    songs = songs["list"]
    album_map = {}
    for song in songs:
        album_id = song["albumCid"]
        if album_id not in album_map:
            album = await get_json(album_url(album_id))
            album_map[album_id] = album
    for album in album_map.values():
        await download_cover(album["name"], album["coverUrl"], album["coverDeUrl"])
        downloading_songs = []
        for song in album["songs"]:
            data = await get_json(song_url(song["cid"]))
            co = download_song(album["name"], data["name"], data["sourceUrl"])
            downloading_songs.append(co)
            co = download_lrc(album["name"], data["name"], data["lyricUrl"])
            downloading_songs.append(co)
        await asyncio.gather(*downloading_songs)


if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
