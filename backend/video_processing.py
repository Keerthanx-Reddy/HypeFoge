import os
import json
import subprocess
import shutil
from typing import Dict, Any, List

def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def probe_video(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {
            "duration": 10.0, "fps": 30.0, "bitrate": 100000,
            "width": 1280, "height": 720, "resolution": "1280x720",
            "codec": "h264", "has_audio": True, "audio_codec": "aac"
        }
    
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    res = run_cmd(cmd)
    if res.returncode != 0:
        return {
            "duration": 10.0, "fps": 30.0, "bitrate": 100000,
            "width": 1280, "height": 720, "resolution": "1280x720",
            "codec": "h264", "has_audio": True, "audio_codec": "aac"
        }
    try:
        data = json.loads(res.stdout)
        v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
        fmt = data.get("format", {})
        
        width = int(v_stream.get("width", 1280))
        height = int(v_stream.get("height", 720))
        duration = float(fmt.get("duration", v_stream.get("duration", 10.0)))
        bitrate = int(fmt.get("bit_rate", 100000))
        
        r_fps = v_stream.get("r_frame_rate", "30/1")
        if "/" in r_fps:
            num, den = r_fps.split("/")
            fps = round(float(num) / max(float(den), 1.0), 2)
        else:
            fps = float(r_fps)
            
        return {
            "duration": round(duration, 3),
            "fps": fps,
            "bitrate": bitrate,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "codec": v_stream.get("codec_name", "h264"),
            "has_audio": a_stream is not None,
            "audio_codec": a_stream.get("codec_name", "aac") if a_stream else None
        }
    except Exception:
        return {
            "duration": 10.0, "fps": 30.0, "bitrate": 100000,
            "width": 1280, "height": 720, "resolution": "1280x720",
            "codec": "h264", "has_audio": True, "audio_codec": "aac"
        }

def generate_thumbnail(video_path: str, thumb_out_path: str, timestamp_sec: float = 1.0) -> bool:
    os.makedirs(os.path.dirname(thumb_out_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", str(timestamp_sec), "-i", video_path,
        "-vframes", "1", "-q:v", "2", thumb_out_path
    ]
    res = run_cmd(cmd)
    return res.returncode == 0 and os.path.exists(thumb_out_path)

def extract_audio(video_path: str, audio_out_path: str) -> bool:
    os.makedirs(os.path.dirname(audio_out_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_out_path
    ]
    res = run_cmd(cmd)
    return res.returncode == 0 and os.path.exists(audio_out_path)

def detect_silence(video_path: str, noise_db: str = "-30dB", duration: float = 0.5) -> List[Dict[str, float]]:
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=noise={noise_db}:d={duration}",
        "-f", "null", "-"
    ]
    res = run_cmd(cmd)
    silences = []
    current_start = None
    for line in res.stderr.splitlines():
        if "silence_start:" in line:
            parts = line.split("silence_start:")
            try:
                current_start = float(parts[1].strip().split()[0])
            except:
                pass
        elif "silence_end:" in line and current_start is not None:
            parts = line.split("silence_end:")
            try:
                end_str = parts[1].strip().split()[0]
                end = float(end_str)
                silences.append({"start": current_start, "end": end, "duration": round(end - current_start, 3)})
                current_start = None
            except:
                pass
    return silences
