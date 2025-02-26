import streamlink
import sys
import os
import json
import traceback

def info_to_text(stream_info, url):
    text = '#EXT-X-STREAM-INF:'
    if stream_info.program_id:
        text += f'PROGRAM-ID={stream_info.program_id},'
    if stream_info.bandwidth:
        text += f'BANDWIDTH={stream_info.bandwidth},'
    if stream_info.codecs:
        text += 'CODECS="'
        codecs = stream_info.codecs
        text += ','.join(codecs)
        text += '",'
    if stream_info.resolution.width and stream_info.resolution.height:
        text += f'RESOLUTION={stream_info.resolution.width}x{stream_info.resolution.height}'
    text += "\n" + url + "\n"
    return text

def main():
    try:
        # Config faylını yüklə
        with open(sys.argv[1], "r") as f:
            config = json.load(f)

        # Çıxış qovluqlarını yoxla və yarat
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
            try:
                url = channel["url"]
                streams = streamlink.streams(url)

                # 'best' axını və multivariant.playlist yoxla
                if 'best' not in streams or not hasattr(streams['best'], 'multivariant') or not hasattr(streams['best'].multivariant, 'playlists'):
                    print(f"No valid HLS stream found for channel {channel['slug']}")
                    continue

                playlists = streams['best'].multivariant.playlists
                previous_res_height = 0
                master_text = ''
                best_text = ''

                # HTTP/HTTPS yoxlaması
                http_flag = url.startswith("http://")
                if http_flag:
                    plugin_name, plugin_type, given_url = streamlink.session.Streamlink().resolve_url(url)

                for playlist in playlists:
                    uri = playlist.uri
                    info = playlist.stream_info
                    if info.video != "audio_only":
                        sub_text = info_to_text(info, uri)
                        if info.resolution.height > previous_res_height:
                            master_text = sub_text + master_text
                            best_text = sub_text
                        else:
                            master_text += sub_text
                        previous_res_height = info.resolution.height

                # HLS versiya əlavə et
                if master_text:
                    if streams['best'].multivariant.version:
                        version_line = f'#EXT-X-VERSION:{streams["best"].multivariant.version}\n'
                        master_text = version_line + master_text
                        best_text = version_line + best_text
                    master_text = '#EXTM3U\n' + master_text
                    best_text = '#EXTM3U\n' + best_text

                # HTTPS -> HTTP çevrilməsi
                if http_flag and plugin_name == "cinergroup":
                    master_text = master_text.replace("https://", "http://")
                    best_text = best_text.replace("https://", "http://")

                # Faylları yadda saxla
                master_file_path = os.path.join(master_folder, channel["slug"] + ".m3u8")
                best_file_path = os.path.join(best_folder, channel["slug"] + ".m3u8")
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
                print(f"Error processing channel {channel['slug']}: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
