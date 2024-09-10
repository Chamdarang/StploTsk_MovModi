db_connect_info = "postgresql+asyncpg://postgres:root@localhost/movmodi"

local_origin_file_path = "./storage/origin/"
local_processed_file_path = "./storage/modi/"
allowed_media_types = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "mpeg", "3gp", "webm"]
allowed_audio_codecs = ['aac', 'ac3', 'ac3_fixed', 'flac', 'opus', 'libfdk_aac', 'libmp3lame', 'libopus', 'libvorbis',
                        'libwavpack', 'libshine', 'libtwolame', 'libvo_amrwbenc', 'libilbc', 'libspeex']
allowed_video_codecs = ['h264', 'libx264', 'hevc', 'libx265', 'libvpx', 'libxvid', 'mpeg4', 'libopenjpeg', 'libtheora',
                        'libxavs', 'libxavs2', 'libaom-av1', 'gif', 'png', 'mjpeg', 'libvpx-vp9', 'libx264rgb',
                        'libx265', 'libopenh264', 'libsvtav1']
