import streamlink
import sys
import os
import json

def info_to_text(stream_info, url):
    text = '#EXT-X-STREAM-INF:'
    if stream_info.program_id:
        text += f'PROGRAM-ID={stream_info.program_id},'
    if stream_info.bandwidth:
        text += f'BANDWIDTH={stream_info.bandwidth},'
    if stream_info.codecs:
        text += 'CODECS="'
        codecs = stream_info.codecs
        for i in range(len(codecs)):
            text += codecs[i]
            if len(codecs) - 1 != i:
                text += ','
        text += '",'
    if stream_info.resolution.width:
        text += f'RESOLUTION={stream_info.resolution.width}x{stream_info.resolution.height}' 

    text += f"\n{url}\n"
    return text

def main():
    # Config faylını yükləyirik
    try:
        with open(sys.argv[1], "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Config faylını yükləmə zamanı səhv: {e}")
        sys.exit(1)

    # Çıxış seçimlərini əldə edirik və qovluqlar yaradırıq
    folder_name = config["output"]["folder"]
    best_folder_name = config["output"]["bestFolder"]
    master_folder_name = config["output"]["masterFolder"]
    current_dir = os.getcwd()
    root_folder = os.path.join(current_dir, folder_name)
    best_folder = os.path.join(root_folder, best_folder_name)
    master_folder = os.path.join(root_folder, master_folder_name)
    os.makedirs(best_folder, exist_ok=True)
    os.makedirs(master_folder, exist_ok=True)

    channels = config["channels"]
    for channel in channels:
        # Streamləri və playlistləri əldə edirik
        try:
            url = channel["url"]
            streams = streamlink.streams(url)
            
            if 'best' not in streams or not hasattr(streams['best'], 'multivariant') or not hasattr(streams['best'].multivariant, 'playlists'):
                print(f"URL üçün keçərli playlistlər tapılmadı: {url}")
                continue

            playlists = streams['best'].multivariant.playlists

            # Mətn hazırlığı
            previous_res_height = 0
            master_text = ''
            best_text = ''

            # http/https seçimlərini yoxlayırıq
            http_flag = False
            if url.startswith("http://"):
                plugin_name, plugin_type, given_url = streamlink.session.Streamlink().resolve_url(url)
                http_flag = True

            for playlist in playlists:
                uri = playlist.uri
                info = playlist.stream_info
                # Sub-playlistləri təsnif edirik
                if info.video != "audio_only": 
                    sub_text = info_to_text(info, uri)
                    if info.resolution.height > previous_res_height:
                        master_text = sub_text + master_text
                        best_text = sub_text
                    else:
                        master_text += sub_text
                    previous_res_height = info.resolution.height
            
            # HLS üçün zəruri dəyərlər
            if master_text:
                if streams['best'].multivariant.version:
                    master_text = f'#EXT-X-VERSION:{streams['best'].multivariant.version}\n' + master_text
                    best_text = f'#EXT-X-VERSION:{streams['best'].multivariant.version}\n' + best_text
                master_text = '#EXTM3U\n' + master_text
                best_text = '#EXTM3U\n' + best_text

            # cinergroup plugin üçün HTTPS -> HTTP
            if http_flag:
                if plugin_name == "cinergroup":
                    master_text = master_text.replace("https://", "http://")
                    best_text = best_text.replace("https://", "http://")

            # Fayl əməliyyatları
            master_file_path = os.path.join(master_folder, f"{channel['slug']}.m3u8")
            best_file_path = os.path.join(best_folder, f"{channel['slug']}.m3u8")

            if master_text:
                with open(master_file_path, "w+") as master_file:
                    master_file.write(master_text)

                with open(best_file_path, "w+") as best_file:
                    best_file.write(best_text)
                
            else:
                if os.path.isfile(master_file_path):
                    os.remove(master_file_path)
                if os.path.isfile(best_file_path):
                    os.remove(best_file_path)
        except Exception as e:
            print(f"Kanal {channel['slug']} üçün səhv: {e}")
            master_file_path = os.path.join(master_folder, f"{channel['slug']}.m3u8")
            best_file_path = os.path.join(best_folder, f"{channel['slug']}.m3u8")
            if os.path.isfile(master_file_path):
                os.remove(master_file_path)
            if os.path.isfile(best_file_path):
                os.remove(best_file_path)

if __name__ == "__main__":
    main()
