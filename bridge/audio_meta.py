"""Audio header facts without external tools (the file's REAL sample rate/channels; duration where the header has it)."""
import os, struct

_MP3_SR = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}
_AAC_SR = (96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350)


def header_info(path):
    info = {"sr": None, "ch": None, "bits": None, "codec": None, "duration": None}
    try:
        with open(path, "rb") as f:
            head = f.read(65536)
        ext = os.path.splitext(path)[1].lower()
        if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
            pos = 12
            data_size = None
            while pos + 8 <= len(head):
                cid, size = head[pos:pos + 4], struct.unpack("<I", head[pos + 4:pos + 8])[0]
                if cid == b"fmt " and pos + 24 <= len(head):
                    tag, ch, sr, _br, _ba, bits = struct.unpack("<HHIIHH", head[pos + 8:pos + 24])
                    info.update(sr=sr, ch=ch, bits=bits, codec="float" if tag == 3 else "pcm")
                elif cid == b"data":
                    data_size = size if size != 0xFFFFFFFF else None
                    break
                pos += 8 + size + (size & 1)
            if data_size and info["sr"] and info["ch"] and info["bits"]:
                info["duration"] = data_size / (info["sr"] * info["ch"] * info["bits"] / 8)
        elif ext == ".mp3" or head[:3] == b"ID3" or head[:1] == b"\xff":
            p = 0
            if head[:3] == b"ID3":
                p = 10 + ((head[6] & 0x7F) << 21 | (head[7] & 0x7F) << 14 | (head[8] & 0x7F) << 7 | (head[9] & 0x7F))
                with open(path, "rb") as f:
                    f.seek(p); head = f.read(8192); p = 0
            while p + 4 <= len(head):
                if head[p] == 0xFF and (head[p + 1] & 0xE0) == 0xE0:
                    ver = (head[p + 1] >> 3) & 3; sr_i = (head[p + 2] >> 2) & 3
                    if ver != 1 and sr_i != 3 and ver in _MP3_SR:
                        info.update(sr=_MP3_SR[ver][sr_i], ch=1 if (head[p + 3] >> 6) == 3 else 2, codec="mp3"); break
                p += 1
        elif ext in (".aac",) and head[:1] == b"\xff":
            info.update(sr=_AAC_SR[(head[2] >> 2) & 15], ch=((head[2] & 1) << 2) | (head[3] >> 6), codec="aac")
    except (OSError, IndexError, struct.error):
        pass
    return info
